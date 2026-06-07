Giọng mẫu được load từ ref_info.json (không quét .txt tự động).

Ví dụ assets/ref_info.json:

{
  "yen_nhi": {
    "name": "Yến Nhi",
    "audio_path": "data/ref_audio/yen_nhi.wav",
    "text": "nội dung lời nói trong file wav..."   ← BẮT BUỘC (không auto transcribe)
  }
}

audio_path tìm theo thứ tự:
  assets/<path>
  <project_root>/<path>
  data/ref_audio/<tên file>

Sau khi sửa JSON, bấm "Làm mới danh sách" trên GUI.
