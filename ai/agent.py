import json
import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from providers.base import BaseDataProvider
from ai.prompts import SYSTEM_PROMPT_TEMPLATE

class BIAgent:
    def __init__(self, data_provider: BaseDataProvider):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.data_provider = data_provider
        self.model_name = "gemini-3.6-flash"

    def get_tools(self):
        execute_sql_func = types.FunctionDeclaration(
            name="execute_sql",
            description="Veritabanında DuckDB SQL sorgusu çalıştırır ve sonuçları döner.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "sql_query": types.Schema(
                        type="STRING",
                        description="Tablo adının 'sales' olduğu geçerli SQL sorgusu"
                    )
                },
                required=["sql_query"]
            )
        )

        generate_chart_func = types.FunctionDeclaration(
            name="generate_chart",
            description="Sorgu sonucuna göre ekrana çizilecek grafik konfigürasyonunu oluşturur.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "chart_type": types.Schema(type="STRING", enum=["bar", "line", "pie"]),
                    "title": types.Schema(type="STRING"),
                    "x_column": types.Schema(type="STRING"),
                    "y_column": types.Schema(type="STRING")
                },
                required=["chart_type", "title", "x_column", "y_column"]
            )
        )
        return [types.Tool(function_declarations=[execute_sql_func, generate_chart_func])]

    def _generate_with_retry(self, contents, config, max_retries=3):
        """API isteklerini yöneten ve 503/429 hatalarında otomatik bekleyip tekrar deneyen yardımcı fonksiyon"""
        for attempt in range(max_retries):
            try:
                return self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
            except APIError as e:
                error_msg = str(e)
                # Sadece aşırı yüklenme (503) veya kota sınırı (429) hatalarında tekrar dene
                if ("503" in error_msg or "429" in error_msg) and attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)  # 3, 6 sn bekler
                    time.sleep(wait_time)
                else:
                    raise e

    def chat(self, user_message: str, history: list):
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(db_schema=self.data_provider.get_schema())
        
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=self.get_tools(),
            temperature=0.1
        )

        # 1. Sohbet geçmişinde None veya boş içerik kalmasını engelliyoruz
        contents = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            text_content = str(msg.get("content") or " ")
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text_content)]))
        
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        # İlk modeli çağırma (Retry mantığı ile)
        response = self._generate_with_retry(contents, config)

        last_df = None
        chart_config = None

        # 2. Döngü ile birden fazla araç çağrısını (SQL + Grafik) sıralı işliyoruz
        while response.function_calls:
            contents.append(response.candidates[0].content)
            
            tool_response_parts = []
            for call in response.function_calls:
                tool_name = call.name
                tool_inputs = call.args or {}
                tool_result_content = ""

                if tool_name == "execute_sql":
                    try:
                        sql = tool_inputs.get("sql_query", "")
                        df = self.data_provider.run_query(sql)
                        last_df = df
                        tool_result_content = df.to_json(orient="records")
                    except Exception as e:
                        tool_result_content = f"Hata: {str(e)}"

                elif tool_name == "generate_chart":
                    chart_config = dict(tool_inputs)
                    tool_result_content = "Grafik konfigürasyonu başarıyla kaydedildi."

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": tool_result_content}
                    )
                )

            contents.append(types.Content(
                role="user",
                parts=tool_response_parts
            ))

            # Araç yanıtından sonra modeli tekrar çağırma (Retry mantığı ile)
            response = self._generate_with_retry(contents, config)

        final_text = response.text or ""

        # 3. Yanıtın None dönmesini kesin olarak engelliyoruz
        if not final_text.strip():
            if chart_config:
                final_text = "İstediğiniz grafik oluşturuldu."
            elif last_df is not None:
                final_text = "Veri sorgulandı ve sonuçlar hazırlandı."
            else:
                final_text = "İşleminiz tamamlandı."

        return final_text, last_df, chart_config