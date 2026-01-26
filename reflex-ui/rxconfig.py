import os
import reflex as rx

config = rx.Config(
    app_name="vapor",
    app_module_import="vapor.chat",
    api_url=os.getenv("API_URL", "http://localhost:8000"),
    plugins=[rx.plugins.SitemapPlugin()],
)
