import json
import os
from anthropic import Anthropic
from providers.base import BaseDataProvider
from ai.prompts import SYSTEM_PROMPT_TEMPLATE

class BIAgent:
    def __init__(self, data_provider: BaseDataProvider):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.data_provider = data_provider
        self.model = "claude-3-5-sonnet-20241022"

    def get_tools(self):
        return [
            {
                "name": "execute_sql",
                "description": "Veritabanında SQL sorgusu çalıştırır ve sonuçları döner.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql_query": {"type": "string", "description": "Çalıştırılacak geçerli SQL sorgusu"}
                    },
                    "required": ["sql_query"]
                }
            },
            {
                "name": "generate_chart",
                "description": "Sorgu sonucuna göre grafik konfigürasyonu oluşturur.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                        "title": {"type": "string"},
                        "x_column": {"type": "string"},
                        "y_column": {"type": "string"}
                    },
                    "required": ["chart_type", "title", "x_column", "y_column"]
                }
            }
        ]

    def chat(self, user_message: str, history: list):
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(db_schema=self.data_provider.get_schema())
        messages = history + [{"role": "user", "content": user_message}]
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            tools=self.get_tools(),
            messages=messages
        )

        last_df = None
        chart_config = None

        while response.stop_reason == "tool_use":
            tool_use_block = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use_block.name
            tool_inputs = tool_use_block.input
            tool_use_id = tool_use_block.id

            tool_result_content = ""

            if tool_name == "execute_sql":
                try:
                    df = self.data_provider.run_query(tool_inputs["sql_query"])
                    last_df = df
                    tool_result_content = df.to_json(orient="records")
                except Exception as e:
                    tool_result_content = f"Hata: {str(e)}"

            elif tool_name == "generate_chart":
                chart_config = tool_inputs
                tool_result_content = "Grafik konfigürasyonu başarıyla kaydedildi."

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": tool_result_content
                    }
                ]
            })

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                tools=self.get_tools(),
                messages=messages
            )

        final_text = next((block.text for block in response.content if block.type == "text"), "")
        return final_text, last_df, chart_config