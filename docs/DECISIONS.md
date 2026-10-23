# Decisions

บันทึกการตัดสินใจเชิงออกแบบที่ไม่ได้ระบุใน `docs/SPEC.md` รูปแบบ: บริบท → ตัวเลือก → เลือก → เหตุผล

---

## D-001 Vercel entrypoint: ใช้ `[tool.vercel]` ชี้ไปที่ `app.main:app` แทน `api/index.py`
*Phase 0 · 2026-10-23 · เจ้าของโปรเจกต์อนุมัติแล้ว (ต่างจากสเปก section 4)*

- **บริบท:** สเปก section 4 กำหนด `api/index.py` เป็น entrypoint แต่เอกสาร Vercel Python runtime ฉบับปัจจุบันบอกว่า "A Python framework preset takes precedence over file-based functions … files under `/api` don't become separate Vercel Functions" และ `app/main.py` อยู่ในรายชื่อไฟล์ที่ FastAPI preset ตรวจหาอัตโนมัติ แปลว่าถ้ามี `api/index.py` ไฟล์นั้นจะไม่ถูกใช้
- **ตัวเลือก:** (1) `[tool.vercel] entrypoint = "app.main:app"` ตามที่ Vercel แนะนำสำหรับโปรเจกต์ใหม่ (2) คง `api/index.py` แล้วชี้ entrypoint ไปที่ไฟล์นั้น (3) ทำตามสเปกตรงตัวพร้อม rewrites
- **เลือก:** (1) และไม่สร้าง `api/index.py`
- **เหตุผล:** ตรงกับเอกสารปัจจุบัน, ไม่มีไฟล์ที่ไม่ถูกใช้, ระบุ entrypoint ชัดแทนการพึ่ง auto-detect, ไม่ต้องมี rewrites เพราะ preset ส่งทุก request เข้า app

## D-002 `vercel.json` มีแค่ `$schema` ใน Phase 0
- **บริบท:** สเปกระบุว่า `vercel.json` ใช้สำหรับ rewrites และ crons
- **ตัวเลือก:** ใส่ `functions` (maxDuration, excludeFiles) ตั้งแต่ตอนนี้ / ใส่เฉพาะที่จำเป็น
- **เลือก:** มีแค่ `$schema` ไว้ให้ editor ช่วยเติม ส่วน crons เพิ่มใน Phase 5
- **เหตุผล:** FastAPI preset ไม่ต้องใช้ rewrites, และถ้า key ใน `functions` ไม่ตรงกับ function ที่ Vercel สร้าง deploy จะล้มเหลว จึงไม่ใส่สิ่งที่ยังไม่จำเป็น

## D-003 ตรึง Python เป็น 3.13 ทั้งใน `.python-version` และ `requires-python = "==3.13.*"`
- **บริบท:** Vercel อ่านเวอร์ชันจาก `pyproject.toml` หรือ `.python-version` แต่เอกสารไม่ได้บอกว่าแหล่งไหนชนะ และรองรับ 3.12 (default), 3.13, 3.14
- **เลือก:** ระบุตรงกันทั้งสองที่ และใช้ `==3.13.*` แทน `>=3.13`
- **เหตุผล:** กัน Vercel เลือก 3.14 จากช่วง `>=` ทำให้เครื่อง, CI และ production ใช้เวอร์ชันเดียวกัน

## D-004 Config: เพิ่ม field ทีละ phase, default เป็น production, ไม่สนค่าว่าง
- **บริบท:** สเปกให้รายการ env ครบทุก phase ใน section 2.4
- **เลือก:**
  - `Settings` มีเฉพาะ field ที่ phase นั้นใช้ (`extra="ignore"` จึงกรอก `.env.local` ครบได้ตั้งแต่วันแรก)
  - `APP_ENV` ค่า default เป็น `production`
  - `env_ignore_empty=True` ให้บรรทัดว่างอย่าง `SUPABASE_URL=` ได้ค่า default แทน `""`
  - อ่าน `.env.local` อัตโนมัติ (บน Vercel ไม่มีไฟล์นี้ จึงใช้ env จริง)
  - `ADMIN_EMAILS` แปลงเป็นตัวพิมพ์เล็กตั้งแต่ตอนโหลด
- **เหตุผล:** ถ้าลืมตั้ง `APP_ENV` บน Vercel ระบบจะปลอดภัยไว้ก่อน (ไม่ mount static, ไม่เปิด API docs) และค่าว่างจะไม่หลุดผ่าน validation เป็นสตริงว่าง

## D-005 ใช้ app factory `create_app(settings)` พร้อม `app` ระดับ module
- **เหตุผล:** Vercel ต้องการตัวแปร `app` ระดับ module ส่วน test ต้องสร้าง app ด้วย config ต่างกัน (development/production) โดยไม่ต้องแก้ env ของ process

## D-006 เปิด API docs (`/api/docs`, `/api/openapi.json`) เฉพาะ development
- **เหตุผล:** ลดพื้นผิวที่เปิดสู่สาธารณะบน production และวางไว้ใต้ `/api` ให้ routing เหมือนกันทั้งบนเครื่องและบน Vercel

## D-007 Dependencies
- ใช้ `fastapi` ไม่ใช่ `fastapi[standard]` เพื่อไม่ให้ bundle บน Vercel มี CLI และ extras ที่ไม่ได้ใช้
- `uvicorn` อยู่ใน dev group เพราะ Vercel มี ASGI server ของตัวเอง (**ตรวจตอน deploy ครั้งแรก**: ถ้า build log ฟ้องว่าขาด uvicorn ให้ย้ายไป dependencies หลัก)
- Test client ยังใช้ `httpx` แม้ Starlette 1.x จะเตือนให้ใช้ `httpx2` แทน รอเจ้าของโปรเจกต์อนุมัติการเพิ่ม `httpx2` (โปรเจกต์ใต้ github.com/pydantic/httpx2)

## D-008 Ruff
- rule set: `E, W, F, I, UP, B, SIM, ASYNC, S, ANN, RUF` โดย `ANN` บังคับ type hints ตาม CLAUDE.md และ `S` (bandit) ช่วยจับปัญหา security
- ปิด `RUF001–003` เพราะข้อความภาษาไทยจะถูกเตือนเรื่องอักขระคล้ายกัน
- ยกเว้น `docs/`, `.agents/`, `.claude/` เพราะ ruff 0.17 จัดรูปแบบ code block ใน Markdown ด้วย และจะไปแก้โค้ดตัวอย่างใน SPEC.md

## D-009 CI ตรึง GitHub Actions ด้วย commit SHA
- **บริบท:** `astral-sh/setup-uv` ไม่มี tag แบบ major (`v10`) ให้ใช้
- **เลือก:** ตรึงทั้ง `actions/checkout` และ `setup-uv` ด้วย SHA พร้อม comment บอกเวอร์ชัน
- **เหตุผล:** ป้องกัน tag ถูกย้ายไปชี้โค้ดอื่น (supply chain) อัปเดตได้ด้วย Dependabot ภายหลัง

## D-010 ย้าย `SPEC.md` ไปไว้ที่ `docs/SPEC.md`
*เจ้าของโปรเจกต์อนุมัติแล้ว* ให้ตรงกับ CLAUDE.md และสเปก section 4

## D-011 Windows + Smart App Control (เฉพาะเครื่องพัฒนา)
- **บริบท:** Smart App Control บล็อก `python.exe` ใน `.venv` ที่ uv สร้างจาก Python ที่ uv ดาวน์โหลดเอง (เป็น trampoline ที่ไม่มีลายเซ็น) และบล็อก `pytest.exe`/`uvicorn.exe` ที่ uv สร้าง
- **เลือก:** ติดตั้ง Python 3.13 จาก Python install manager (`py install 3.13` มีลายเซ็น PSF) แล้วสร้าง `.venv` ด้วย `uv venv --python <path>` และบนเครื่องนี้รันเครื่องมือผ่าน `python -m`:
  - `uv run python -m pytest`
  - `uv run python -m uvicorn app.main:app --reload --port 3000`
  - `ruff` เป็น binary ที่รันได้ตามปกติ
- **ผลกระทบ:** ไม่มีผลกับ CI หรือ Vercel (Linux) คำสั่งใน CLAUDE.md ยังใช้ได้ตามเดิมบนเครื่องอื่น
