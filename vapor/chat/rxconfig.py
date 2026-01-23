import reflex as rx

config = rx.Config(
    app_name="vapor",
    app_module_import="vapor.chat",
    plugins=[rx.plugins.SitemapPlugin()],
)
