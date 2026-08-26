import ast
from pathlib import Path
from typing import List, Tuple
from .types import SemanticNode

class SemanticVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.nodes: List[SemanticNode] = []
        self.current_class = None

    def visit_ClassDef(self, node: ast.ClassDef):
        docstring = ast.get_docstring(node) or ""
        self.nodes.append(SemanticNode(
            symbol_name=node.name,
            symbol_type="class",
            file_path=self.file_path,
            line_range=(node.lineno, node.end_lineno or node.lineno),
            docstring=docstring,
            dependencies=[b.id for b in node.bases if isinstance(b, ast.Name)],
            summary=f"Class {node.name}" + (f": {docstring[:50]}..." if docstring else "")
        ))
        
        # Keep track of class context for methods
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        docstring = ast.get_docstring(node) or ""
        name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        self.nodes.append(SemanticNode(
            symbol_name=name,
            symbol_type="function",
            file_path=self.file_path,
            line_range=(node.lineno, node.end_lineno or node.lineno),
            docstring=docstring,
            dependencies=[],
            summary=f"Function {name}" + (f": {docstring[:50]}..." if docstring else "")
        ))
        self.generic_visit(node)

class SemanticDistiller:
    def distill_file(self, file_path: Path) -> List[SemanticNode]:
        if not file_path.exists() or file_path.suffix != '.py':
            return []
            
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return []

        visitor = SemanticVisitor(str(file_path))
        visitor.visit(tree)
        
        # Add module level docstring if present
        mod_doc = ast.get_docstring(tree)
        if mod_doc:
            visitor.nodes.insert(0, SemanticNode(
                symbol_name=file_path.stem,
                symbol_type="module",
                file_path=str(file_path),
                line_range=(1, len(content.splitlines())),
                docstring=mod_doc,
                dependencies=[],
                summary=f"Module {file_path.stem}"
            ))
            
        return visitor.nodes

    def distill_directory(self, dir_path: Path) -> List[SemanticNode]:
        nodes = []
        if not dir_path.is_dir():
            return nodes
            
        for py_file in dir_path.rglob("*.py"):
            nodes.extend(self.distill_file(py_file))
        return nodes

    def summarize_context(self, nodes: List[SemanticNode], max_tokens: int = 1000) -> str:
        # A simple character-based approximation for tokens (approx 4 chars per token)
        max_chars = max_tokens * 4
        
        lines = []
        current_chars = 0
        
        for node in nodes:
            entry = f"- {node.symbol_type} `{node.symbol_name}` ({node.file_path}:{node.line_range[0]}-{node.line_range[1]}): {node.summary}"
            if current_chars + len(entry) > max_chars:
                lines.append("... (truncated)")
                break
            lines.append(entry)
            current_chars += len(entry)
            
        return "\n".join(lines)
