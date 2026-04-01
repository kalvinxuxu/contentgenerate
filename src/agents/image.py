"""
配图 Agent (ImageAgent)
为文案生成 Midjourney 提示词和视觉建议，支持 Minimax 图片生成
"""

import json
import os
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .base import Agent, AgentEnvelope
from .prompts.image import SYSTEM_PROMPT, USER_PROMPT, FEW_SHOT_EXAMPLES
from src.utils.llm_client import create_llm_client, call_llm_sync, parse_json_response
from src.utils.prompt_engine import PromptEngine, PromptTemplate
from src.utils.config import get_model_config
from src.utils.minimax_client import MinimaxImageClient

logger = logging.getLogger(__name__)


class ImageAgent(Agent):
    """
    配图 Agent
    视觉创意总监，为文案内容生成 Midjourney 提示词和排版建议
    """

    name = "image_agent"
    description = "视觉创意总监，为文案内容生成 Midjourney 提示词和排版建议"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化配图 Agent

        Args:
            config: 配置字典
        """
        # 获取默认配置
        default_config = get_model_config("image")
        merged_config = {**default_config, **(config or {})}

        super().__init__(merged_config)

        # 初始化 LLM 客户端
        self.llm_client = None

        # 初始化 Minimax 图片生成客户端
        self.minimax_client = None

        # 初始化 Prompt 引擎
        self.prompt_engine = PromptEngine(
            PromptTemplate(
                name="image_agent",
                system_prompt=SYSTEM_PROMPT,
                user_prompt=USER_PROMPT,
                variables=["content", "platform", "emotion", "brand_colors", "style_preference"],
                examples=FEW_SHOT_EXAMPLES
            )
        )

        # 图片保存目录
        self.output_dir = merged_config.get("output_dir", "uploads/generated")

    def initialize(self) -> bool:
        """初始化 LLM 客户端和 Minimax 客户端"""
        try:
            self.llm_client = create_llm_client(
                model=self.config.get("model", "qwen-plus"),
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 2500)
            )

            # 初始化 Minimax 图片生成客户端
            self.minimax_client = MinimaxImageClient()

            self._initialized = True
            return True
        except Exception as e:
            print(f"初始化 ImageAgent 失败：{e}")
            return False

    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """验证输入"""
        valid, missing = self._validate_payload(
            payload,
            required_fields=["content", "platform", "emotion"]
        )
        if not valid:
            print(f"输入验证失败，缺失字段：{missing}")
            return False
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """返回输入 Schema"""
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "文案内容"},
                "platform": {"type": "string", "description": "发布平台"},
                "emotion": {"type": "string", "description": "情绪基调"},
                "brand_colors": {"type": "array", "items": {"type": "string"}},
                "style_preference": {"type": "string", "description": "风格偏好"},
                "reference_image_path": {"type": "string", "description": "参考图路径（图生图模式）"},
                "generate_image": {"type": "boolean", "description": "是否生成实际图片（默认 true）"},
                "image_strength": {"type": "number", "description": "图生图参考强度，0-1，默认 0.75"},
            },
            "required": ["content", "platform", "emotion"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """返回输出 Schema"""
        return {
            "type": "object",
            "properties": {
                "mj_prompts": {"type": "array", "description": "Midjourney 提示词（备选方案）"},
                "layout_suggestions": {"type": "object"},
                "color_palette": {"type": "object"},
                "font_recommendations": {"type": "array"},
                "rationale": {"type": "string"},
                "generated_images": {"type": "array", "description": "Minimax 生成的图片路径列表"},
                "image_metadata": {"type": "object", "description": "图片生成元数据"}
            }
        }

    def process(self, envelope: AgentEnvelope) -> AgentEnvelope:
        """
        处理配图请求

        Args:
            envelope: 输入信封

        Returns:
            输出信封
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("ImageAgent 未初始化")

        # 验证输入
        if not self.validate_input(envelope.payload):
            raise ValueError("输入验证失败")

        # 提取输入参数
        content = envelope.payload.get("content", "")
        platform = envelope.payload.get("platform", "xiaohongshu")
        emotion = envelope.payload.get("emotion", "hopeful")
        brand_colors = envelope.payload.get("brand_colors", [])
        style_preference = envelope.payload.get("style_preference", "minimalist")
        reference_image_path = envelope.payload.get("reference_image_path")
        generate_image = envelope.payload.get("generate_image", True)
        image_strength = envelope.payload.get("image_strength", 0.75)
        num_images = envelope.payload.get("num_images", 1)  # 生成图片数量

        # 渲染 Prompt
        system_prompt, user_prompt = self.prompt_engine.render(
            {
                "content": content,
                "platform": platform,
                "emotion": emotion,
                "brand_colors": brand_colors if brand_colors else "无特定要求",
                "style_preference": style_preference
            },
            include_examples=True
        )

        # 调用 LLM 生成视觉创意方案
        logger.info("正在生成视觉创意方案...")
        response = call_llm_sync(
            self.llm_client,
            system_prompt,
            user_prompt
        )

        # 解析 JSON 响应
        try:
            result = parse_json_response(response)
        except json.JSONDecodeError as e:
            retry_prompt = f"请将以下内容解析为 JSON 格式：\n\n{response}"
            response = call_llm_sync(self.llm_client, system_prompt, retry_prompt)
            result = parse_json_response(response)

        # 如果需要生成实际图片
        generated_images = []
        image_metadata = {}

        if generate_image and self.minimax_client:
            try:
                # 确保输出目录存在
                output_dir = Path(self.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                # 从 LLM 结果中提取最佳 prompt
                mj_prompts = result.get("mj_prompts", [])
                if mj_prompts and len(mj_prompts) > 0:
                    best_prompt = mj_prompts[0].get("prompt_en", "")
                    prompt_cn = mj_prompts[0].get("prompt_cn", "")
                else:
                    best_prompt = f"Professional {emotion} image, {style_preference} style"
                    prompt_cn = f"专业{emotion}图片，{style_preference}风格"

                # 根据平台获取推荐的宽高比
                aspect_ratio = self.minimax_client.get_aspect_ratio_for_platform(platform)
                logger.info(f"使用宽高比：{aspect_ratio} (平台：{platform})")

                # 生成指定数量的图片
                timestamp = int(time.time())
                mode_name = "subject_reference" if reference_image_path else "text2image"
                logger.info(f"开始生成 {num_images} 张图片 ({mode_name}模式)...")

                for i in range(num_images):
                    try:
                        if reference_image_path:
                            # 图生图模式（主体参考）
                            logger.info(f"生成图片 {i+1}/{num_images} (图生图)...")
                            gen_result = self.minimax_client.generate_and_save(
                                prompt=best_prompt,
                                reference_image_path=reference_image_path,
                                subject_type="character",  # Minimax API 仅支持 character 类型
                                aspect_ratio=aspect_ratio,
                                save_path=str(output_dir / f"image_{timestamp}_{i+1}.png"),
                                num_images=1
                            )
                            image_metadata[f"image_{i+1}"] = {
                                "mode": "subject_reference",
                                "reference_image": reference_image_path,
                                "subject_type": "character"
                            }
                        else:
                            # 文生图模式
                            logger.info(f"生成图片 {i+1}/{num_images} (文生图)...")
                            gen_result = self.minimax_client.generate_and_save(
                                prompt=best_prompt,
                                aspect_ratio=aspect_ratio,
                                save_path=str(output_dir / f"image_{timestamp}_{i+1}.png"),
                                num_images=1
                            )
                            image_metadata[f"image_{i+1}"] = {
                                "mode": "text2image"
                            }

                        # 收集生成的图片路径
                        if "saved_path" in gen_result:
                            generated_images.append(gen_result["saved_path"])
                            logger.info(f"图片 {i+1} 保存成功：{gen_result['saved_path_relative']}")

                    except Exception as e:
                        logger.error(f"图片 {i+1} 生成失败：{e}")
                        image_metadata[f"image_{i+1}_error"] = str(e)

                # 记录元数据
                image_metadata["total_requested"] = num_images
                image_metadata["total_generated"] = len(generated_images)
                image_metadata["prompt_used"] = best_prompt
                image_metadata["prompt_cn"] = prompt_cn
                image_metadata["aspect_ratio"] = aspect_ratio

            except Exception as e:
                logger.error(f"图片生成失败：{e}")
                image_metadata["error"] = str(e)

        # 添加生成的图片信息到结果
        result["generated_images"] = generated_images
        result["image_metadata"] = image_metadata

        # 创建输出信封
        output_envelope = self._create_output_envelope(envelope, result)

        # 添加到上下文
        output_envelope.add_to_context("image_output", result)

        return output_envelope
