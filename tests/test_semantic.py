import tempfile
from pathlib import Path
from swarmmemory.semantic import SemanticDistiller

def test_distill_file():
    code = '''
"""Module docstring."""
class MyClass:
    """Class docstring."""
    def my_method(self):
        """Method docstring."""
        pass

def my_func():
    pass
'''
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "dummy.py"
        p.write_text(code, encoding='utf-8')
        
        distiller = SemanticDistiller()
        nodes = distiller.distill_file(p)
        
        assert len(nodes) == 4
        
        types = {n.symbol_type for n in nodes}
        assert types == {"module", "class", "function"}
        
        names = {n.symbol_name for n in nodes}
        assert "dummy" in names
        assert "MyClass" in names
        assert "MyClass.my_method" in names
        assert "my_func" in names

def test_summarize_context():
    distiller = SemanticDistiller()
    code = '''class Foo:\n    def bar(self):\n        pass'''
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "dummy2.py"
        p.write_text(code, encoding='utf-8')
        nodes = distiller.distill_file(p)
        
        summary = distiller.summarize_context(nodes, max_tokens=100)
        assert "Foo" in summary
        assert "Foo.bar" in summary
