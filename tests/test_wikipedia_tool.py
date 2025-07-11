
from src.agent.tools.wikipedia_search_tool import WikipediaSearchTool


class TestWikipediaTool:
    def setup_method(self):
        # Default language English
        self.tool = WikipediaSearchTool(lang="en")
        
    def test_run_page_not_found(self):
        # Query nonsense to trigger PageError
        result = self.tool.run("asdkjasldkjalksjdlkajsd")
        assert result == "No page found for that query."

    def test_run_unexpected_error(self, monkeypatch):
        # Monkeypatch wikipedia.page to raise a generic exception
        def mock_page(query):
            raise Exception("Unexpected error")
        monkeypatch.setattr("wikipedia.page", mock_page)

        result = self.tool.run("Python")
        assert result.startswith("Error: Unexpected error")
