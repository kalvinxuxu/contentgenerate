"""
多 Agent 文案生成系统 - CLI 入口
"""

import os
import sys
import click
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from dotenv import load_dotenv

# Windows 终端 UTF-8 编码支持
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# 加载环境变量
load_dotenv()

from src.workflow import WorkflowOrchestrator
from src.utils.config import get_model_config

console = Console()

# 兼容 GBK 编码的符号
CHECK_MARK = "[green]OK[/green]"  # ✓
CROSS_MARK = "[red]X[/red]"       # ✗
DASH_MARK = "-"                   # —


@click.group()
@click.version_option(version="0.1.0", prog_name="content-agent")
def cli():
    """多 Agent 文案生成系统

    使用 AI Agent 工作流自动生成爆款文案
    """
    pass


@cli.command()
@click.option("--topic", "-t", required=True, help="内容主题")
@click.option("--audience", "-a", default="", help="目标受众")
@click.option("--platform", "-p", default="xiaohongshu",
              type=click.Choice(["xiaohongshu", "wechat", "blog"]),
              help="发布平台")
@click.option("--tone", default="casual",
              type=click.Choice(["casual", "formal", "passionate"]),
              help="语气风格")
@click.option("--priority", default="standard",
              type=click.Choice(["quick", "standard", "deep"]),
              help="优化优先级")
@click.option("--emotion", default="hopeful", help="情绪基调")
@click.option("--style", default="minimalist", help="视觉风格偏好")
@click.option("--brand-keywords", "-k", multiple=True, help="品牌关键词")
@click.option("--output", "-o", type=click.Path(), help="输出文件路径")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def generate(topic, audience, platform, tone, priority, emotion, style, brand_keywords, output, verbose):
    """运行完整文案生成工作流"""

    console.print(Panel.fit(
        f"[bold blue]多 Agent 文案生成系统[/bold blue]\n"
        f"主题：{topic}\n"
        f"平台：{platform} | 语气：{tone} | 优先级：{priority}",
        box=box.ROUNDED
    ))

    # 初始化工作流
    console.print("\n[dim]初始化工作流...[/dim]")
    orchestrator = WorkflowOrchestrator()

    try:
        # 运行工作流
        result = orchestrator.run(
            topic=topic,
            target_audience=audience,
            platform=platform,
            tone=tone,
            priority=priority,
            brand_keywords=list(brand_keywords),
            style_preference=style,
            emotion=emotion
        )

        # 显示结果
        console.print("\n[bold green]OK 生成完成[/bold green]\n")

        # 显示步骤状态
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE)
        table.add_column("步骤", style="cyan")
        table.add_column("状态", justify="center")

        for step in result.get("steps", []):
            status = CHECK_MARK if step["status"] == "completed" else DASH_MARK if step["status"] == "skipped" else CROSS_MARK
            style = "green" if step["status"] == "completed" else "yellow" if step["status"] == "skipped" else "red"
            table.add_row(step["name"], f"[{style}]{status}[/{style}]")

        console.print(table)

        # 显示最终内容
        final_output = result.get("final_output", {})

        console.print("\n[bold]最终文案[/bold]")
        console.print(Panel(
            final_output.get("final_content", ""),
            title="文案内容",
            box=box.ROUNDED,
            border_style="blue"
        ))

        # 显示审核结果
        reviewer = final_output.get("reviewer", {})
        if reviewer:
            console.print("\n[bold]审核结果[/bold]")
            console.print(f"总体评分：{reviewer.get('overall_score', 'N/A')}/6")
            console.print(f"审核结论：{reviewer.get('conclusion', 'N/A')}")

            highlights = reviewer.get("highlights", [])
            if highlights:
                console.print("\n[green]亮点:[/green]")
                for h in highlights:
                    console.print(f"  - {h}")

        # 显示配图建议
        image = final_output.get("image", {})
        if image:
            console.print("\n[bold]配图建议[/bold]")
            mj_prompts = image.get("mj_prompts", [])
            for i, prompt in enumerate(mj_prompts, 1):
                console.print(f"\n[cyan]方案{i}: {prompt.get('style', '')}[/cyan]")
                console.print(f"[dim]{prompt.get('prompt_en', '')}[/dim]")

        # 保存到文件
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            console.print(f"\n[green]OK 结果已保存到：{output}[/green]")

    except Exception as e:
        console.print(f"\n[bold red]X 执行失败：{e}[/bold red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise SystemExit(1)


@cli.command()
def config():
    """显示当前配置"""

    console.print("[bold]当前配置[/bold]\n")

    agents = ["research", "creator", "reviewer", "optimizer", "image"]

    table = Table(show_header=True, header_style="bold", box=box.SIMPLE_HEAD)
    table.add_column("Agent", style="cyan")
    table.add_column("Model")
    table.add_column("Temperature")
    table.add_column("Max Tokens")

    for agent in agents:
        try:
            config = get_model_config(agent)
            table.add_row(
                agent,
                config.get("model", "N/A"),
                str(config.get("temperature", "N/A")),
                str(config.get("max_tokens", "N/A"))
            )
        except Exception:
            table.add_row(agent, "N/A", "N/A", "N/A")

    console.print(table)


@cli.command()
@click.option("--topic", "-t", required=True, help="内容主题")
@click.option("--audience", "-a", default="", help="目标受众")
@click.option("--platform", "-p", default="xiaohongshu", help="发布平台")
def research(topic, audience, platform):
    """仅运行调研 Agent"""
    from src.agents.research import ResearchAgent
    from src.agents.base import AgentEnvelope

    console.print("[bold]运行调研 Agent...[/bold]\n")

    agent = ResearchAgent(get_model_config("research"))
    agent.initialize()

    envelope = AgentEnvelope(
        source_agent="user",
        target_agent="research_agent",
        payload={
            "topic": topic,
            "target_audience": audience,
            "platform": platform,
            "brand_keywords": []
        }
    )

    result = agent.process(envelope)

    output = result.payload

    console.print(f"[bold]趋势分析[/bold]")
    console.print(output.get("trend_analysis", "") + "\n")

    console.print(f"[bold]用户痛点[/bold]")
    for pain in output.get("pain_points", []):
        console.print(f"  • {pain.get('title')}: {pain.get('description')}")

    console.print(f"\n[bold]选题切入点[/bold]")
    for angle in output.get("angles", []):
        console.print(f"  • {angle.get('headline')} (置信度：{angle.get('confidence_score', 0):.0%})")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
def review(input_file):
    """审核文案文件"""
    from src.agents.reviewer import ReviewerAgent
    from src.agents.base import AgentEnvelope
    from src.agents.prompts.reviewer import USER_PROMPT

    console.print("[bold]运行审核 Agent...[/bold]\n")

    # 读取文件
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 尝试解析 JSON 或纯文本
    try:
        data = json.loads(content)
        draft = data.get("body", data.get("content", ""))
        content_type = data.get("content_type", "社交媒体文案")
        platform = data.get("platform", "xiaohongshu")
    except json.JSONDecodeError:
        draft = content
        content_type = "社交媒体文案"
        platform = "xiaohongshu"

    agent = ReviewerAgent(get_model_config("reviewer"))
    agent.initialize()

    envelope = AgentEnvelope(
        source_agent="user",
        target_agent="reviewer_agent",
        payload={
            "content_type": content_type,
            "platform": platform,
            "draft": draft
        }
    )

    result = agent.process(envelope)
    output = result.payload

    # 显示结果
    console.print(f"[bold]总体评分[/bold]: {output.get('overall_score', 'N/A')}/6")
    console.print(f"[bold]审核结论[/bold]: {output.get('conclusion', 'N/A')}\n")

    console.print(f"[bold]维度评分[/bold]")
    for dim in output.get("dimension_scores", []):
        score = dim.get("score", 0)
        bar = "=" * score + "-" * (5 - score)
        console.print(f"  {dim.get('dimension')}: [{bar}] {score}/5 - {dim.get('comment', '')}")

    highlights = output.get("highlights", [])
    if highlights:
        console.print(f"\n[green]亮点[/green]")
        for h in highlights:
            console.print(f"  OK {h}")

    issues = output.get("must_fix_issues", [])
    if issues:
        console.print(f"\n[red]必须修改的问题[/red]")
        for issue in issues:
            console.print(f"  [{issue.get('location')}] {issue.get('problem')}")
            console.print(f"     建议：{issue.get('suggestion')}")


def main():
    """CLI 主入口"""
    cli()


if __name__ == "__main__":
    main()
