import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MarkdownExporter:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, source_filename: str, data: Dict[str, Any]) -> Path:
        base = Path(source_filename).stem
        out_path = self.output_dir / f"{base}.md"

        # Формируем YAML frontmatter + Markdown тело (Obsidian-совместимый)
        lines = ["---"]
        for k, v in data.items():
            if isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{k}: {v}")
        lines.append("---\n")

        lines.append(f"# {base.replace('_', ' ').title()}\n")
        lines.append(f"**Дата:** {data.get('date', 'N/A')}\n")
        lines.append(f"**Резюме:** {data.get('summary', 'N/A')}\n")
        lines.append("\n### 📋 Задачи")
        for task in data.get("action_items", []):
            lines.append(f"- [ ] {task}")
        lines.append("\n### 🏷️ Теги")
        lines.append(" ".join(f"#{tag}" for tag in data.get("tags", [])))

        out_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"📄 Exported: {out_path.name}")
        return out_path
