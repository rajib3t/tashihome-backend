"""Model package.

Keep this module free of eager imports so submodule imports like
`app.models.token_model` do not trigger database/config initialization
as a side effect.
"""
