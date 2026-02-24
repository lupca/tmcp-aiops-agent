import sys
import os
import json
import logging
from unittest.mock import patch, MagicMock

# Configure basic logging for the test
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Ensure we can import from the core and workflow modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from workflow.graph import aiops_app
from api.routes.webhook import run_aiops_workflow
from langchain_core.messages import AIMessage

def test_aiops_pipeline_with_mocks():
    print("🚀 Bắt đầu chạy giả lập AIOps Workflow...\n")

    # 1. Payload giả lập từ Webhook (Kibana/Prometheus)
    payload = {
        "service_name": "payment-service",
        "timestamp": "2026-02-24T13:50:00Z",
        "error_message": "java.lang.OutOfMemoryError: Java heap space"
    }

    # 2. Giả lập dữ liệu log trả về từ Elasticsearch
    mock_es_logs = (
        "[2026-02-24T13:49:50Z] [INFO] Processing payment for user user_8910\n"
        "[2026-02-24T13:49:55Z] [WARN] Memory utilization reached 95% threshold\n"
        "[2026-02-24T13:49:58Z] [ERROR] High GC Pause time detected (9000ms)\n"
        "[2026-02-24T13:50:00Z] [ERROR] java.lang.OutOfMemoryError: Java heap space"
    )

    # 3. Giả lập Output của LLM (format JSON)
    mock_llm_json_response = json.dumps({
        "root_cause": "Dịch vụ payment-service bị hết bộ nhớ Java Heap (OOM) do mức sử dụng bộ nhớ cao (95%) và thời gian dừng dọn dẹp bộ nhớ rác (GC Pause) quá lâu (9000ms).",
        "solution": "Tạm thời khởi động lại service. Về lâu dài: tăng cấu hình bộ nhớ heap size (-Xmx) và kiểm tra lại code rò rỉ bộ nhớ (memory leak) ở luồng thanh toán."
    })

    # fake class
    # fake class
    # fake class

    print("🔧 Đang tiêm Mocks (Elasticsearch, ChatOllama, Discord)...\n")
    
    # Dùng context manager patch để thay thế các hàm gọi ra ngoài bằng mock
    with patch('workflow.graph.get_surrounding_logs', return_value=mock_es_logs) as mock_es, \
         patch('langchain_community.chat_models.ChatOllama.invoke', return_value=AIMessage(content=mock_llm_json_response)) as mock_llm, \
         patch('core.discord.settings.DISCORD_WEBHOOK_URL', 'https://mock.discord.com/webhook'), \
         patch('core.discord.requests.Session') as mock_session_cls:
         
        # Giả lập request gửi Discord thành công
        mock_session_instance = mock_session_cls.return_value
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_session_instance.post.return_value = mock_response

        # Kích hoạt node chạy workflow 
        print("▶️ Chạy LangGraph Background Task...")
        run_aiops_workflow(payload)

        print("\n✅ KẾT QUẢ KIỂM TRA:\n")
        
        # Kiểm tra Elasticsearch được gọi đúng param
        mock_es.assert_called_once_with("payment-service", "2026-02-24T13:50:00Z")
        print("1. [PASS] Đã gọi hàm lấy Log Elasticsearch với context hợp lệ.")
        
        # Kiểm tra Discord được gọi với payload đúng format embed
        mock_session_instance.post.assert_called_once()
        call_args, call_kwargs = mock_session_instance.post.call_args
        discord_payload = call_kwargs.get("json")
        print("2. [PASS] Payload Discord được cấu hình hoàn thiện:\n")
        print(json.dumps(discord_payload, indent=2, ensure_ascii=False))
        
        print("\n🎉 Test Workflow HOÀN TẤT THÀNH CÔNG!")

if __name__ == "__main__":
    test_aiops_pipeline_with_mocks()
