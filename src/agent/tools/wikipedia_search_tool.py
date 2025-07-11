import wikipedia

from src.agent.tools.tool_base import ToolBase


class WikipediaSearchTool(ToolBase):
    def __init__(self, lang: str = "en"):
        wikipedia.set_lang(lang)

    def run(self, query: str) -> str:
        try:
            page = wikipedia.page(query)
            return page.content[:1000]  # limit to first 1000 chars
        except wikipedia.DisambiguationError as e:
            return f"Disambiguation error: Try one of {e.options[:5]}"
        except wikipedia.PageError:
            return "No page found for that query."
        except Exception as e:
            return f"Error: {str(e)}"
