# CLAUDE.md — ShopFlow

ระบบรับออเดอร์อัตโนมัติจาก LINE สำหรับร้านค้ารายย่อย (portfolio project, ใช้แพ็กเกจฟรีทั้งหมด)
Stack: FastAPI on Vercel · Supabase (Postgres, Auth, pg_cron) · Gemini API · LINE Messaging API · Make.com · vanilla HTML/CSS/JS

**อ่าน `docs/SPEC.md` ก่อนเริ่มงานทุกครั้ง** สเปกนั้นเป็นแหล่งความจริงหลัก ถ้าสิ่งที่ขอขัดกับสเปก ให้ถามก่อนทำ

## วิธีทำงาน

- ทำทีละ phase ตาม SPEC.md section 12 จบ phase แล้ว **หยุด** สรุปสิ่งที่ทำและวิธีทดสอบ ให้เจ้าของโปรเจกต์รีวิวก่อน
- เปลี่ยนแปลงทีละน้อย commit เล็ก ๆ ข้อความ commit แบบ Conventional Commits ภาษาอังกฤษ (`feat:`, `fix:`, `test:`, `docs:`)
- เขียน test พร้อมโค้ด รัน test และ lint ให้ผ่านก่อนบอกว่างานเสร็จ
- ตรวจเอกสารฉบับปัจจุบันของ Vercel Python runtime, Supabase, LINE SDK และ Google GenAI SDK ก่อนใช้ API หรือ config ที่ไม่แน่ใจ เพราะบริการเหล่านี้เปลี่ยนบ่อย
- ทุกการตัดสินใจเชิงออกแบบที่ไม่ได้ระบุในสเปก ให้บันทึกสั้น ๆ ใน `docs/DECISIONS.md` (บริบท → ตัวเลือก → เลือกอะไร → เพราะอะไร)

## คำสั่งที่ใช้บ่อย

```bash
uv sync                          # ติดตั้ง dependencies
uv run pytest                    # รัน test
uv run ruff check . && uv run ruff format --check .
uv run uvicorn app.main:app --reload --port 3000   # รันบนเครื่อง (mount public/ เฉพาะ APP_ENV=development)
supabase db push                 # apply migrations (ถามเจ้าของก่อนทุกครั้ง)
# Deploy: git push เท่านั้น (Vercel เชื่อมกับ GitHub อยู่แล้ว) ไม่ต้องใช้ Vercel CLI
# Env: คัดลอก .env.example เป็น .env.local แล้วให้เจ้าของโปรเจกต์กรอกเอง
# Windows ที่เปิด Smart App Control: ใช้ `uv run python -m pytest` / `uv run python -m uvicorn ...` (ดู docs/DECISIONS.md D-011)
uv run python evals/run_eval.py --provider gemini --model <name> --delay 4
```

## Conventions

- โค้ด, ชื่อตัวแปร, comment, commit: ภาษาอังกฤษ / ข้อความที่ผู้ใช้เห็น (dashboard, LINE reply): ภาษาไทย / README: ภาษาไทย
- Python: type hints ทุกฟังก์ชันใน `app/`, Pydantic v2, pydantic-settings สำหรับ config
- Business logic อยู่ใน `app/services/` และเป็น pure function ให้มากที่สุด, router บางที่สุด
- เปลี่ยน schema ผ่านไฟล์ใน `supabase/migrations/` เท่านั้น
- Frontend: vanilla JS, ไม่ใช้ build step, โหลด supabase-js จาก CDN, รองรับมือถือ

## ห้ามทำ

- ห้าม commit secret หรือไฟล์ `.env*` (ยกเว้น `.env.example`)
- ห้ามส่งข้อความลูกค้าไป LLM โดยไม่ผ่าน `services/pii.py`
- ห้ามใช้ราคาหรือยอดรวมที่ LLM ส่งมา ต้องคำนวณจากฐานข้อมูล
- ห้ามเรียก API ภายนอกจริงใน test (ใช้ `FakeLLMProvider` และ mock)
- ห้ามรัน eval ใน CI
- ห้ามส่ง phone/address ไป Make.com หรือ Google Sheets
- ห้ามใช้ LINE push สำหรับตอบลูกค้า (ใช้ reply เท่านั้น)
- ห้ามใช้ข้อมูลลูกค้าจริง ใช้ร้านสมมติและข้อมูลสังเคราะห์เท่านั้น

## ต้องถามเจ้าของโปรเจกต์ก่อน

- สร้าง/แก้ทรัพยากรบนคลาวด์ (Vercel project, Supabase, LINE channel, Make scenario)
- รัน migration กับฐานข้อมูลบนคลาวด์ หรือลบข้อมูล
- เพิ่ม dependency ที่ทำให้ bundle บน Vercel ใหญ่ขึ้นมาก
- เปลี่ยนโครงสร้างที่ต่างจาก SPEC.md
- งานที่จะใช้ Make operations หรือ LINE push quota มากผิดปกติ

## การรีวิวโค้ด (สำคัญ)

โปรเจกต์นี้ใช้แสดงทักษะ **รีวิวและทดสอบโค้ดที่ AI เขียน** ดังนั้น:
- ใส่ comment `# REVIEW:` ตรงจุดที่มีความเสี่ยงหรือมีสมมติฐาน (เช่น regex, เงื่อนไข decision, การจัดการ timeout, security) พร้อมบอกสั้น ๆ ว่าควรตรวจอะไร
- จบแต่ละ phase ให้สรุป "จุดที่ควรรีวิว" เป็นรายการ
- **ห้ามเขียนเนื้อหาใน `docs/AI_USAGE.md` แทนเจ้าของโปรเจกต์** ไฟล์นั้นเจ้าของเขียนเองจากประสบการณ์รีวิวจริง (สร้างได้แค่ template หัวข้อว่างใน Phase 7)
