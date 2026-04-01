"""
多 Agent 文案生成系统 - FastAPI 后端
支持图片上传和分阶段确认机制
"""

import os
import sys
import asyncio
import uuid
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 线程池用于运行同步阻塞的工作流
executor = ThreadPoolExecutor(max_workers=4)

# 全局事件循环
main_event_loop = None

from dotenv import load_dotenv
load_dotenv()

from src.workflow import WorkflowOrchestrator
from src.utils.config import get_model_config

# 图片上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 结果保存目录
RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def save_task_result(task_id: str, config: dict, step_results: dict, final_output: dict):
    """保存任务结果到 JSON 文件

    Args:
        task_id: 任务 ID
        config: 任务配置
        step_results: 各步骤结果
        final_output: 最终输出
    """
    result_data = {
        "task_id": task_id,
        "created_at": datetime.now().isoformat(),
        "config": config,
        "step_results": step_results,
        "final_output": final_output
    }

    # 保存到文件
    filepath = os.path.join(RESULTS_DIR, f"{task_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"结果已保存到：{filepath}")
    return filepath

app = FastAPI(
    title="多 Agent 文案生成系统 API",
    description="提供文案生成的 REST API 和 WebSocket 实时进度推送",
    version="2.0.0"
)

# 启动时保存主事件循环
@app.on_event("startup")
async def startup_event():
    global main_event_loop
    main_event_loop = asyncio.get_event_loop()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（用于访问上传的图片）
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 存储运行中的任务
running_tasks: Dict[str, Dict[str, Any]] = {}

# 分阶段工作流状态
workflow_states: Dict[str, Dict[str, Any]] = {}


class StepResult(BaseModel):
    """单步结果"""
    status: str
    data: Optional[Dict[str, Any]] = None
    message: str = ""


class StepConfirmRequest(BaseModel):
    """步骤确认请求"""
    action: str  # "continue" 或 "modify"
    modifications: Optional[Dict[str, Any]] = None  # 用户修改内容


# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_message(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_json(message)
            except:
                self.disconnect(task_id)

manager = ConnectionManager()


# ============== 数据模型 ==============

class GenerateRequest(BaseModel):
    """文案生成请求"""
    topic: str = Field(..., description="内容主题")
    audience: str = Field(default="", description="目标受众")
    platform: str = Field(default="xiaohongshu", description="发布平台")
    tone: str = Field(default="casual", description="语气风格")
    priority: str = Field(default="standard", description="优化优先级")
    emotion: str = Field(default="hopeful", description="情绪基调")
    style: str = Field(default="minimalist", description="视觉风格")
    brand_keywords: List[str] = Field(default=[], description="品牌关键词")
    product_image_path: Optional[str] = Field(default=None, description="产品图片路径")


class GenerateResponse(BaseModel):
    """文案生成响应"""
    task_id: str
    status: str
    message: str
    created_at: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: int
    current_step: Optional[str]
    current_step_result: Optional[dict]
    steps: List[dict]
    result: Optional[dict]
    awaiting_confirmation: bool
    created_at: str
    updated_at: str


# ============== API 接口 ==============

@app.get("/")
async def root():
    """API 健康检查"""
    return {
        "name": "多 Agent 文案生成系统 API",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """上传产品图片"""
    try:
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        filename = f"{file_id}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # 保存文件
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        # 转换为 base64（用于传递给 LLM）
        with open(filepath, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        return {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "image_base64": image_base64[:1000] + "..."  # 只返回前 1000 字符用于预览
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败：{str(e)}")


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """
    启动分阶段文案生成工作流
    第一阶段：运行调研 Agent，然后等待用户确认
    """
    task_id = str(uuid.uuid4())

    # 初始化任务状态
    running_tasks[task_id] = {
        "task_id": task_id,
        "status": "running",
        "progress": 0,
        "current_step": "调研",
        "current_step_result": None,
        "steps": [
            {"name": "调研", "status": "running", "result": None},
            {"name": "创作", "status": "pending", "result": None},
            {"name": "审核", "status": "pending", "result": None},
            {"name": "优化", "status": "pending", "result": None},
            {"name": "配图", "status": "pending", "result": None}
        ],
        "result": None,
        "awaiting_confirmation": False,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "config": request.dict()
    }

    # 初始化分阶段状态
    workflow_states[task_id] = {
        "current_step_index": 0,
        "step_results": {},
        "status": "running"
    }

    # 启动异步任务
    asyncio.ensure_future(run_step_workflow_in_thread(task_id, request.dict()))

    return GenerateResponse(
        task_id=task_id,
        status="running",
        message="已启动调研阶段",
        created_at=running_tasks[task_id]["created_at"]
    )


@app.post("/api/task/{task_id}/confirm")
async def confirm_step(task_id: str, request: StepConfirmRequest):
    """用户确认当前步骤，继续下一阶段"""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = running_tasks[task_id]

    if not task.get("awaiting_confirmation"):
        raise HTTPException(status_code=400, detail="当前不需要确认")

    if request.action == "continue":
        # 继续下一步
        task["awaiting_confirmation"] = False
        workflow_states[task_id]["status"] = "running"

        # 启动下一步
        asyncio.ensure_future(run_next_step(task_id))

        return {"status": "ok", "message": "继续执行下一阶段"}

    elif request.action == "modify":
        # 用户提供了修改意见，需要重新运行当前步骤
        modifications = request.modifications or {}
        feedback = modifications.get("feedback", "")

        # 保存修改意见到工作流状态
        workflow_states[task_id]["modification_feedback"] = feedback
        workflow_states[task_id]["status"] = "running"

        # 重置 awaiting_confirmation，但不递增步骤索引
        task["awaiting_confirmation"] = False

        # 重新运行当前步骤（不递增步骤索引）
        asyncio.ensure_future(run_current_step_with_modification(task_id, feedback))

        return {"status": "ok", "message": "正在根据您的意见重新生成"}

    elif request.action == "stop":
        # 停止工作流
        task["status"] = "cancelled"
        task["awaiting_confirmation"] = False
        workflow_states[task_id]["status"] = "cancelled"
        return {"status": "ok", "message": "已停止工作流"}

    else:
        raise HTTPException(status_code=400, detail="无效的操作")


@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = running_tasks[task_id]
    return TaskStatusResponse(**task)


# ============== 结果管理 API ==============

@app.get("/api/results")
async def list_results(limit: int = 20):
    """获取历史结果列表"""
    from .results_index import get_results_index

    index = get_results_index()
    results = index.list_results(limit)
    return {"results": results, "total": len(results)}


@app.get("/api/results/search")
async def search_results(q: str, limit: int = 20):
    """搜索结果"""
    from .results_index import get_results_index

    index = get_results_index()
    results = index.search_results(q)
    return {"results": results[:limit], "total": len(results)}


@app.get("/api/results/{task_id}")
async def get_result(task_id: str):
    """获取单个结果"""
    from .results_index import get_results_index

    index = get_results_index()
    result = index.get_result(task_id)

    if result is None:
        raise HTTPException(status_code=404, detail="结果不存在")

    return result


@app.delete("/api/results/{task_id}")
async def delete_result(task_id: str):
    """删除结果"""
    from .results_index import get_results_index

    index = get_results_index()
    success = index.delete_result(task_id)

    if success:
        return {"status": "ok", "message": f"已删除结果：{task_id}"}
    else:
        raise HTTPException(status_code=404, detail="结果不存在")


# ============== 对话历史 API ==============

@app.get("/api/conversations/{task_id}")
async def get_conversation_history(task_id: str):
    """获取对话历史"""
    from .conversation_history import get_conversation_history

    history = get_conversation_history()
    result = history.get_history(task_id)

    if result is None:
        raise HTTPException(status_code=404, detail="对话历史不存在")

    return result


@app.get("/api/conversations/{task_id}/versions")
async def list_versions(task_id: str):
    """列出所有版本"""
    from .conversation_history import get_conversation_history

    history = get_conversation_history()
    versions = history.list_versions(task_id)

    return {"versions": versions, "total": len(versions)}


@app.get("/api/conversations/{task_id}/version/{version_index}")
async def get_version(task_id: str, version_index: int):
    """获取指定版本文案"""
    from .conversation_history import get_conversation_history

    history = get_conversation_history()
    version = history.get_version(task_id, version_index)

    if version is None:
        raise HTTPException(status_code=404, detail="版本不存在")

    return version


@app.post("/api/conversations/{task_id}/restore")
async def restore_version(task_id: str, version_index: int):
    """恢复到指定版本"""
    from .conversation_history import get_conversation_history

    history = get_conversation_history()
    success = history.set_current_version(task_id, version_index)

    if success:
        return {"status": "ok", "message": f"已恢复到版本 {version_index}"}
    else:
        raise HTTPException(status_code=404, detail="版本不存在或恢复失败")


@app.websocket("/ws/task/{task_id}")
async def websocket_task_progress(websocket: WebSocket, task_id: str):
    """WebSocket 实时进度推送"""
    await manager.connect(websocket, task_id)

    # 发送当前状态
    if task_id in running_tasks:
        await manager.send_message(task_id, running_tasks[task_id])

    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息
            if data == "ping":
                await manager.send_message(task_id, {"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(task_id)


# ============== 分阶段工作流 ==============

async def run_step_workflow_in_thread(task_id: str, request_data: dict):
    """在线程池中运行分阶段工作流"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor,
        run_step_workflow_sync,
        task_id,
        request_data
    )


async def run_next_step(task_id: str):
    """运行下一步骤"""
    if task_id not in workflow_states:
        return

    state = workflow_states[task_id]
    task = running_tasks[task_id]

    if state["status"] not in ["running", "pending_confirmation"]:
        return

    step_names = ["调研", "创作", "审核", "优化", "配图"]
    step_index = state["current_step_index"]

    if step_index >= len(step_names):
        # 所有步骤完成
        task["status"] = "completed"
        task["progress"] = 100
        task["current_step"] = "完成"
        task["awaiting_confirmation"] = False

        final_output = task.get("result", {})
        update_task_status(task_id, "completed", 100, "生成完成", result={"final_output": final_output})

        # 保存结果到文件并使用索引管理
        result_data = {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
            "config": task.get("config", {}),
            "step_results": workflow_states[task_id].get("step_results", {}),
            "final_output": final_output
        }

        from .results_index import get_results_index
        index = get_results_index()
        index.add_result(task_id, result_data)

        print(f"结果已保存到：{task_id}.json")
        return

    # 运行当前步骤
    step_name = step_names[step_index]
    update_task_status(task_id, "running", step_index * 20, f"执行{step_name} Agent...")

    # 在线程池中运行同步代码
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            executor,
            run_single_step,
            task_id,
            step_name,
            step_index,
            running_tasks[task_id]["config"]
        )

        # 保存步骤结果
        state["step_results"][step_name] = result
        task["steps"][step_index]["status"] = "completed"
        task["steps"][step_index]["result"] = result

        # 递增步骤索引，为下一步做准备
        state["current_step_index"] = step_index + 1

        # 更新进度
        progress = (step_index + 1) * 20
        update_task_status(
            task_id,
            "pending_confirmation",
            progress,
            f"{step_name}完成，等待确认",
            step_result=result
        )

        # 进入等待确认状态
        task["awaiting_confirmation"] = True
        task["current_step_result"] = result

        # 推送确认请求到前端
        await manager.send_message(task_id, {
            "type": "confirmation_required",
            "step": step_name,
            "step_index": step_index,
            "result": result,
            "message": f"{step_name}已完成，请查看结果后确认是否继续"
        })

    except Exception as e:
        update_task_status(task_id, "failed", step_index * 20, f"{step_name}执行失败：{str(e)}")
        task["status"] = "failed"
        state["status"] = "failed"


def run_single_step(task_id: str, step_name: str, step_index: int, config: dict, modification_feedback: str = None):
    """运行单个步骤

    Args:
        task_id: 任务 ID
        step_name: 步骤名称
        step_index: 步骤索引
        config: 配置字典
        modification_feedback: 用户修改意见（可选）
    """
    config_data = {
        "topic": config["topic"],
        "target_audience": config.get("audience", ""),
        "platform": config.get("platform", "xiaohongshu"),
        "tone": config.get("tone", "casual"),
        "priority": config.get("priority", "standard"),
        "brand_keywords": config.get("brand_keywords", []),
        "style_preference": config.get("style", "minimalist"),
        "emotion": config.get("emotion", "hopeful"),
        "product_image_path": config.get("product_image_path")
    }

    if step_name == "调研":
        return run_research_step(**config_data)
    elif step_name == "创作":
        return run_creator_step(
            research_report=workflow_states[task_id]["step_results"].get("调研", {}),
            tone=config_data["tone"],
            modification_feedback=modification_feedback
        )
    elif step_name == "审核":
        creator_result = workflow_states[task_id]["step_results"].get("创作", {})
        return run_reviewer_step(
            content_type=creator_result.get("content_type", "社交媒体文案"),
            platform=config_data["platform"],
            draft=creator_result.get("body", "")
        )
    elif step_name == "优化":
        creator_result = workflow_states[task_id]["step_results"].get("创作", {})
        reviewer_result = workflow_states[task_id]["step_results"].get("审核", {})
        conclusion = reviewer_result.get("conclusion", "pass")
        if conclusion in ["modify", "rewrite"]:
            return run_optimizer_step(
                original_draft=creator_result.get("body", ""),
                review_report=reviewer_result,
                priority=config_data["priority"],
                modification_feedback=modification_feedback
            )
        return {"status": "skipped", "reason": "审核通过，无需优化"}
    elif step_name == "配图":
        creator_result = workflow_states[task_id]["step_results"].get("创作", {})
        optimizer_result = workflow_states[task_id]["step_results"].get("优化", {})
        final_content = optimizer_result.get("optimized_content", creator_result.get("body", ""))
        return run_image_step(
            content=final_content,
            platform=config_data["platform"],
            emotion=config_data["emotion"],
            style_preference=config_data["style_preference"],
            reference_image_path=config_data.get("product_image_path"),
            generate_image=True  # 启用实际图片生成
        )
    else:
        raise ValueError(f"未知步骤：{step_name}")


def run_step_workflow_sync(task_id: str, request_data: dict):
    """同步版本的分阶段工作流入口"""
    # 第一步直接运行
    asyncio.run_coroutine_threadsafe(
        run_next_step(task_id),
        main_event_loop
    )


async def run_current_step_with_modification(task_id: str, feedback: str):
    """重新运行当前步骤（带修改意见）"""
    if task_id not in workflow_states:
        return

    state = workflow_states[task_id]
    task = running_tasks[task_id]

    step_names = ["调研", "创作", "审核", "优化", "配图"]
    # 获取当前步骤索引（因为还没递增，所以是当前步骤）
    step_index = state["current_step_index"]

    if step_index >= len(step_names):
        return

    step_name = step_names[step_index]

    # 更新状态为运行中
    update_task_status(task_id, "running", step_index * 20, f"执行{step_name} Agent（根据修改意见重新生成）...")

    # 在线程池中运行同步代码
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            executor,
            run_single_step,
            task_id,
            step_name,
            step_index,
            running_tasks[task_id]["config"],
            feedback  # 传递修改意见
        )

        # 保存步骤结果
        state["step_results"][step_name] = result
        task["steps"][step_index]["status"] = "completed"
        task["steps"][step_index]["result"] = result

        # 保存到对话历史（记录修改意见和新结果）
        from .conversation_history import get_conversation_history
        conv_history = get_conversation_history()

        # 构建完整的结果数据
        result_data = {
            "task_id": task_id,
            "created_at": datetime.now().isoformat(),
            "config": task.get("config", {}),
            "step_results": state["step_results"],
            "final_output": {
                step_name: result
            }
        }

        # 添加对话记录
        conv_history.add_turn(
            task_id=task_id,
            user_feedback=feedback,
            new_result=result_data,
            version_index=None  # 自动分配版本号
        )

        # 更新进度
        progress = (step_index + 1) * 20
        update_task_status(
            task_id,
            "pending_confirmation",
            progress,
            f"{step_name}完成（已根据修改意见重新生成）",
            step_result=result
        )

        # 进入等待确认状态
        task["awaiting_confirmation"] = True
        task["current_step_result"] = result

        # 推送确认请求到前端
        await manager.send_message(task_id, {
            "type": "confirmation_required",
            "step": step_name,
            "step_index": step_index,
            "result": result,
            "message": f"{step_name}已根据修改意见重新生成，请查看结果后确认是否继续"
        })

    except Exception as e:
        update_task_status(task_id, "failed", step_index * 20, f"{step_name}执行失败：{str(e)}")
        task["status"] = "failed"
        state["status"] = "failed"


def run_research_step(topic, target_audience, platform, brand_keywords, product_image_path=None, **kwargs):
    """运行调研 Agent"""
    from src.agents.research import ResearchAgent
    from src.agents.base import AgentEnvelope
    from src.utils.config import get_model_config

    config = get_model_config("research")
    agent = ResearchAgent(config)
    agent.initialize()

    payload = {
        "topic": topic,
        "target_audience": target_audience,
        "platform": platform,
        "brand_keywords": brand_keywords
    }

    # 如果有产品图片，添加到 payload
    if product_image_path:
        payload["product_image"] = product_image_path

    envelope = AgentEnvelope(
        version="1.0",
        source_agent="user",
        target_agent="research_agent",
        payload=payload
    )
    output = agent.process(envelope)
    return output.payload


def run_creator_step(research_report, tone, modification_feedback=None):
    """运行创作 Agent

    Args:
        research_report: 调研报告
        tone: 语气风格
        modification_feedback: 用户修改意见（可选）
    """
    from src.agents.creator import CreatorAgent
    from src.agents.base import AgentEnvelope
    from src.utils.config import get_model_config

    config = get_model_config("creator")
    agent = CreatorAgent(config)
    agent.initialize()

    angles = research_report.get("angles", [])
    selected_angle = angles[0] if angles else {}

    payload = {
        "research_report": research_report,
        "selected_angle": selected_angle,
        "tone": tone
    }

    # 如果有修改意见，添加到 payload 中
    if modification_feedback:
        payload["modification_feedback"] = modification_feedback

    envelope = AgentEnvelope(
        version="1.0",
        source_agent="research_agent",
        target_agent="creator_agent",
        payload=payload,
        context={"research_output": research_report}
    )
    output = agent.process(envelope)
    return output.payload


def run_reviewer_step(content_type, platform, draft):
    """运行审核 Agent"""
    from src.agents.reviewer import ReviewerAgent
    from src.agents.base import AgentEnvelope
    from src.utils.config import get_model_config

    config = get_model_config("reviewer")
    agent = ReviewerAgent(config)
    agent.initialize()

    envelope = AgentEnvelope(
        version="1.0",
        source_agent="creator_agent",
        target_agent="reviewer_agent",
        payload={
            "content_type": content_type,
            "platform": platform,
            "draft": draft
        }
    )
    output = agent.process(envelope)
    return output.payload


def run_optimizer_step(original_draft, review_report, priority, modification_feedback=None):
    """运行优化 Agent

    Args:
        original_draft: 原始草稿
        review_report: 审核报告
        priority: 优化优先级
        modification_feedback: 用户修改意见（可选）
    """
    from src.agents.optimizer import OptimizerAgent
    from src.agents.base import AgentEnvelope
    from src.utils.config import get_model_config

    config = get_model_config("optimizer")
    agent = OptimizerAgent(config)
    agent.initialize()

    payload = {
        "original_draft": original_draft,
        "review_report": review_report,
        "priority": priority
    }

    # 如果有修改意见，添加到 payload 中
    if modification_feedback:
        payload["modification_feedback"] = modification_feedback

    envelope = AgentEnvelope(
        version="1.0",
        source_agent="reviewer_agent",
        target_agent="optimizer_agent",
        payload=payload
    )
    output = agent.process(envelope)
    return output.payload


def run_image_step(content, platform, emotion, style_preference, reference_image_path=None, generate_image=True):
    """运行配图 Agent

    Args:
        content: 文案内容
        platform: 发布平台
        emotion: 情绪基调
        style_preference: 风格偏好
        reference_image_path: 参考图片路径（用于图生图）
        generate_image: 是否生成实际图片（默认 True）
    """
    from src.agents.image import ImageAgent
    from src.agents.base import AgentEnvelope
    from src.utils.config import get_model_config

    config = get_model_config("image")
    agent = ImageAgent(config)
    agent.initialize()

    envelope = AgentEnvelope(
        version="1.0",
        source_agent="optimizer_agent",
        target_agent="image_agent",
        payload={
            "content": content,
            "platform": platform,
            "emotion": emotion,
            "style_preference": style_preference,
            "reference_image_path": reference_image_path,
            "generate_image": generate_image,
            "image_strength": 0.75  # 图生图参考强度
        }
    )
    output = agent.process(envelope)
    return output.payload


def update_task_status(
    task_id: str,
    status: str,
    progress: int,
    current_step: Optional[str],
    step_result: Optional[dict] = None,
    result: Optional[dict] = None
):
    """更新任务状态并推送给前端"""
    task = running_tasks.get(task_id)
    if not task:
        return

    task["status"] = status
    task["progress"] = progress
    task["current_step"] = current_step
    task["updated_at"] = datetime.now().isoformat()

    if step_result is not None:
        task["current_step_result"] = step_result

    if result:
        task["result"] = result

    # 更新步骤状态
    step_names = ["调研", "创作", "审核", "优化", "配图"]
    for i, step in enumerate(task["steps"]):
        if status == "running":
            if i < len(step_names) and step_names[i] in current_step:
                step["status"] = "running"
        elif status in ["completed", "pending_confirmation"]:
            if i < len(step_names) and step_names[i] == current_step.split("完成")[0]:
                step["status"] = "completed"
        elif status == "failed":
            if step["status"] != "completed":
                step["status"] = "failed"

    # 通过 WebSocket 推送状态
    if main_event_loop:
        try:
            asyncio.run_coroutine_threadsafe(
                manager.send_message(task_id, task.copy()),
                main_event_loop
            )
        except Exception as e:
            print(f"WebSocket 推送失败：{e}")


# ============== 启动服务器 ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
