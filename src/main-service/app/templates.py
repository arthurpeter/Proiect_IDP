EMAIL_TEMPLATES = {
    "modern_professional": {
        "style_name": "Modern Professional (Blue)",
        "placeholders": ["subject", "header_title", "main_text", "action_url", "button_label", "footer_text"],
        "html": """
        <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e1e4e8; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <div style="background-color: #007bff; padding: 30px; text-align: center; color: white;">
                <h1 style="margin: 0; font-size: 24px;">{{header_title}}</h1>
            </div>
            <div style="padding: 30px; color: #24292e; line-height: 1.6;">
                <p style="font-size: 16px;">{{main_text}}</p>
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{{action_url}}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">{{button_label}}</a>
                </div>
            </div>
            <div style="background-color: #f6f8fa; padding: 15px; text-align: center; color: #586069; font-size: 12px;">
                {{footer_text}}
            </div>
        </div>
        """
    },
    "minimalist_clean": {
        "style_name": "Minimalist Clean (White)",
        "placeholders": ["subject", "header_title", "main_text", "footer_text"],
        "html": """
        <div style="font-family: Georgia, serif; max-width: 550px; margin: 40px auto; color: #333;">
            <h2 style="border-bottom: 2px solid #333; padding-bottom: 10px; letter-spacing: 1px;">{{header_title}}</h2>
            <div style="padding: 20px 0; font-size: 17px; line-height: 1.8;">
                {{main_text}}
            </div>
            <p style="margin-top: 40px; font-style: italic; color: #888; font-size: 13px; text-align: center;">
                {{footer_text}}
            </p>
        </div>
        """
    },
    "bold_alert": {
        "style_name": "Bold Alert (Red)",
        "placeholders": ["subject", "alert_title", "alert_message", "action_url", "button_label"],
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border-top: 8px solid #dc3545; background-color: #fff5f5; padding: 25px; border-radius: 0 0 8px 8px;">
            <h2 style="color: #c82333; margin-top: 0;">⚠️ {{alert_title}}</h2>
            <div style="background-color: white; padding: 20px; border-radius: 4px; border: 1px solid #ffc107;">
                <p style="margin: 0; color: #856404;">{{alert_message}}</p>
            </div>
            <div style="margin-top: 25px;">
                <a href="{{action_url}}" style="color: #dc3545; font-weight: bold; text-decoration: underline;">{{button_label}}</a>
            </div>
        </div>
        """
    },
    "elegant_soft": {
        "style_name": "Elegant Soft (Purple)",
        "placeholders": ["subject", "title", "content", "sign_off"],
        "html": """
        <div style="background-color: #f4f0f9; padding: 40px; font-family: 'Verdana', sans-serif;">
            <div style="background-color: #ffffff; max-width: 500px; margin: auto; padding: 40px; border-radius: 20px; border: 1px solid #e0d4f1;">
                <h1 style="color: #6f42c1; text-align: center;">{{title}}</h1>
                <div style="color: #555; font-size: 15px; margin: 25px 0;">
                    {{content}}
                </div>
                <p style="text-align: right; color: #6f42c1; font-weight: bold;">{{sign_off}}</p>
            </div>
        </div>
        """
    }
}