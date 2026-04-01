"""
Prompt 引擎
使用 Jinja2 进行模板渲染
"""

from typing import Dict, Any, List, Optional
from jinja2 import Environment, BaseLoader


class PromptTemplate:
    """Prompt 模板类"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        user_prompt: str,
        variables: Optional[List[str]] = None,
        examples: Optional[List[Dict[str, Any]]] = None
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.variables = variables or []
        self.examples = examples or []


class PromptEngine:
    """
    Prompt 引擎
    负责模板渲染和 Few-shot 示例管理
    """

    def __init__(self, template: PromptTemplate):
        """
        初始化 Prompt 引擎

        Args:
            template: Prompt 模板
        """
        self.template = template
        self.env = Environment(
            loader=BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render(
        self,
        variables: Dict[str, Any],
        include_examples: bool = False
    ) -> tuple[str, str]:
        """
        渲染 Prompt

        Args:
            variables: 变量字典
            include_examples: 是否包含示例

        Returns:
            (system_prompt, user_prompt)
        """
        # 渲染 user prompt
        user_template = self.env.from_string(self.template.user_prompt)
        user_prompt = user_template.render(**variables)

        # 添加示例
        if include_examples and self.template.examples:
            examples_text = "\n\n## 示例\n\n"
            for i, example in enumerate(self.template.examples, 1):
                examples_text += f"### 示例 {i}\n"
                if "input" in example:
                    examples_text += f"输入：{example['input']}\n"
                if "output" in example:
                    examples_text += f"输出：{example['output']}\n"
            user_prompt += examples_text

        return self.template.system_prompt, user_prompt

    def render_user_prompt(self, variables: Dict[str, Any]) -> str:
        """
        仅渲染 User Prompt

        Args:
            variables: 变量字典

        Returns:
            渲染后的 User Prompt
        """
        template = self.env.from_string(self.template.user_prompt)
        return template.render(**variables)

    def with_few_shot(
        self,
        examples: List[Dict[str, Any]],
        input_key: str = "input",
        output_key: str = "output"
    ) -> str:
        """
        生成 Few-shot 示例文本

        Args:
            examples: 示例列表
            input_key: 输入键名
            output_key: 输出键名

        Returns:
            Few-shot 文本
        """
        result = ""
        for example in examples:
            result += f"输入：{example.get(input_key, '')}\n"
            result += f"输出：{example.get(output_key, '')}\n\n"
        return result.strip()

    @staticmethod
    def create_template(
        name: str,
        system_prompt: str,
        user_prompt: str,
        variables: Optional[List[str]] = None
    ) -> PromptTemplate:
        """
        静态方法：创建 Prompt 模板

        Args:
            name: 模板名称
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            variables: 变量列表

        Returns:
            PromptTemplate 实例
        """
        return PromptTemplate(
            name=name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            variables=variables
        )
