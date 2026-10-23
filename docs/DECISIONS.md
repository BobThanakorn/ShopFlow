# Decisions

บันทึกการตัดสินใจเชิงออกแบบที่ไม่ได้ระบุใน `docs/SPEC.md`
รูปแบบทุกข้อ: **บริบท → ตัวเลือก → เลือก → เหตุผล**

---

## D-001 Vercel entrypoint: ใช้ `[tool.vercel]` ชี้ไปที่ `app.main:app` แทน `api/index.py`
*Phase 0 · 2026-10-23 · เจ้าของโปรเจกต์อนุมัติแล้ว (ต่างจากสเปก section 4)*
- **บริบท:** สเปก section 4 กำหนด `api/index.py` แต่เอกสาร Vercel ฉบับปัจจุบันบอกว่า "A Python framework preset takes precedence over file-based functions" และ FastAPI preset ตรวจหา `app/main.py` อัตโนมัติ ไฟล์ `api/index.py` จึงจะไม่ถูกใช้
- **ตัวเลือก:** (1) `[tool.vercel] entrypoint = "app.main:app"` (2) คง `api/index.py` แล้วชี้ entrypoint ไปที่ไฟล์นั้น (3) ทำตามสเปกตรงตัวพร้อม rewrites
- **เลือก:** (1) และไม่สร้าง `api/index.py`
- **เหตุผล:** ตรงกับที่ Vercel แนะนำสำหรับโปรเจกต์ใหม่, ไม่มีไฟล์ที่ไม่ถูกใช้, ระบุ entrypoint ชัด และไม่ต้องมี rewrites

## D-002 `vercel.json` มีแค่ `$schema` ใน Phase 0
- **บริบท:** สเปกระบุว่า `vercel.json` ใช้สำหรับ rewrites และ crons แต่ preset ไม่ต้องใช้ rewrites และ crons ยังไม่มีจนถึง Phase 5
- **ตัวเลือก:** (1) ใส่ `functions` (maxDuration, excludeFiles) ไว้เลย (2) ใส่แค่ `$schema`
- **เลือก:** (2) แล้วเพิ่ม crons ใน Phase 5
- **เหตุผล:** ถ้า key ใน `functions` ไม่ตรงกับ function ที่ Vercel สร้าง deploy จะล้มเหลว จึงไม่ใส่สิ่งที่ยังไม่จำเป็น

## D-003 ตรึง Python เป็น 3.13 ด้วย `.python-version` และ `requires-python = "==3.13.*"`
- **บริบท:** Vercel อ่านเวอร์ชันได้จากทั้ง `pyproject.toml` และ `.python-version` แต่ไม่ได้บอกว่าแหล่งไหนชนะ และรองรับทั้ง 3.12, 3.13, 3.14
- **ตัวเลือก:** (1) `.python-version` อย่างเดียว (2) `requires-python = ">=3.13"` (3) ระบุตรงกันทั้งสองที่ด้วย `==3.13.*`
- **เลือก:** (3) ส่วน ruff อนุมาน `target-version` จาก `requires-python` เอง จึงไม่ต้องระบุซ้ำเป็นที่ที่สาม
- **เหตุผล:** เครื่อง, CI และ production ใช้เวอร์ชันเดียวกัน และกัน Vercel เลือก 3.14 จากช่วง `>=` ตอนอัปเกรดแก้แค่สองที่

## D-004 Settings: เพิ่มทีละ phase, fail-safe และตรวจค่าตั้งแต่ตอนเริ่ม
- **บริบท:** section 2.4 ให้ env ครบทุก phase แต่ Phase 0 ใช้แค่บางตัว และ config ที่ผิดควรพังตั้งแต่ตอน startup ไม่ใช่ตอนใช้งานจริง
- **ตัวเลือก:** (1) ประกาศทุก field ตั้งแต่ตอนนี้ (2) เพิ่ม field ตาม phase ที่ใช้ และ ignore ตัวที่ยังไม่ประกาศ
- **เลือก:** (2) พร้อมกฎดังนี้
  - `APP_ENV` ค่า default เป็น `production`
  - `env_ignore_empty=True` ให้ `SUPABASE_URL=` ได้ค่า default แทน `""`
  - อ่าน `.env.local` จาก path ที่ผูกกับ root ของ repo ไม่ใช่ path สัมพัทธ์จาก cwd
  - `ADMIN_EMAILS` แปลงเป็นตัวพิมพ์เล็ก
  - `APP_BASE_URL` ต้องเป็น http(s) URL และเก็บแบบไม่มี `/` ท้าย
  - `SHOP_TIMEZONE` ต้องเป็น IANA timezone ที่มีอยู่จริง
- **เหตุผล:**
  - ถ้าลืมตั้ง `APP_ENV` ระบบจะไม่ mount static และไม่เปิด API docs
  - ถ้ารัน uvicorn จากโฟลเดอร์อื่น ก็ยังโหลด `.env.local` ได้
  - URL หรือ timezone ที่พิมพ์ผิดจะพังตั้งแต่ตอนเริ่ม ไม่ใช่ตอนส่งสรุปยอดตอนสองทุ่ม
  - ข้อเสียของ `extra="ignore"`: ชื่อตัวแปรที่พิมพ์ผิดจะถูกทิ้งเงียบ ๆ (มี `# REVIEW:` กำกับไว้)

## D-005 App factory `create_app(settings)` พร้อม `app` ระดับ module
- **บริบท:** Vercel ต้องการตัวแปร `app` ระดับ module แต่ test ต้องสร้าง app ทั้งแบบ development และ production
- **ตัวเลือก:** (1) `app` ระดับ module อย่างเดียว แล้วใน test แก้ env และ reload module (2) factory ที่รับ `Settings` แล้วสร้าง `app = create_app()` ไว้ระดับ module
- **เลือก:** (2)
- **เหตุผล:** test ส่ง config เข้าไปตรง ๆ ได้ ไม่ต้อง reload module หรือแก้ env ของ process

## D-006 เปิด API docs (`/api/docs`, `/api/openapi.json`) เฉพาะ development
- **บริบท:** FastAPI เปิด `/docs` และ `/openapi.json` ให้โดยอัตโนมัติ ซึ่งบน production จะเปิดเผยรายการ endpoint ทั้งหมด
- **ตัวเลือก:** (1) ใช้ค่า default ของ FastAPI (2) ปิดทุกที่ (3) เปิดเฉพาะ development และย้ายไปไว้ใต้ `/api`
- **เลือก:** (3)
- **เหตุผล:** ลดพื้นผิวที่เปิดบน production แต่ยังมี docs ไว้ใช้ตอนพัฒนา และการอยู่ใต้ `/api` ทำให้ routing เหมือนกันทั้งบนเครื่องและบน Vercel

## D-007 Dependencies ของ runtime
- **บริบท:** ทุก package ใน `dependencies` จะเข้าไปอยู่ใน bundle บน Vercel
- **ตัวเลือก:** `fastapi[standard]` หรือ `fastapi` / uvicorn เป็น dependency หลักหรืออยู่ใน dev / จะพึ่ง tz database ของระบบหรือใช้ `tzdata`
- **เลือก:**
  - `fastapi` (ไม่ใช้ `[standard]`)
  - `uvicorn` อยู่ใน dev group
  - เพิ่ม `tzdata`
  - test client ยังใช้ `httpx`
- **เหตุผล:**
  - ไม่เอา CLI และ extras ที่ไม่ได้ใช้เข้า bundle
  - Vercel มี ASGI server ของตัวเอง (**ต้องตรวจตอน deploy ครั้งแรก**: ถ้า build log ฟ้องว่าขาด uvicorn ให้ย้ายไปเป็น dependency หลัก)
  - Windows และ image Linux แบบ slim ไม่มี tz database ทำให้ `ZoneInfo("Asia/Bangkok")` พัง (ทดสอบแล้วบนเครื่องพัฒนา) และ Phase 5 ต้องใช้คำนวณเวลาตาม `SHOP_TIMEZONE` อยู่แล้ว
  - Starlette 1.x แนะนำให้ใช้ `httpx2` แทน แต่ยังรอเจ้าของโปรเจกต์อนุมัติ
- **หมายเหตุ:** `tzdata` (ประมาณ 1.7 MB หลังติดตั้ง) ถูกเพิ่มเข้าไปก่อนแล้วค่อยแจ้งเจ้าของโปรเจกต์ ไม่ได้ขออนุมัติก่อน ถือว่าไม่ทำให้ bundle "ใหญ่ขึ้นมาก" ตาม CLAUDE.md แต่ยังรอให้เจ้าของโปรเจกต์ยืนยัน

## D-008 Ruff
- **บริบท:** CLAUDE.md บังคับ type hints ใน `app/` และโปรเจกต์นี้เน้นเรื่อง security แต่ข้อความภาษาไทยทำให้บาง rule เตือนผิด และ ruff 0.17 จัดรูปแบบ code block ใน Markdown ด้วย
- **ตัวเลือก:** (1) ใช้ rule ตั้งต้นของ ruff (2) เลือก rule set เอง แล้วปิดเฉพาะ rule ที่เตือนผิด
- **เลือก:** (2) ใช้ `E, W, F, I, UP, B, SIM, ASYNC, S, ANN, RUF`, ปิด `RUF001–003`, และยกเว้น `docs/`, `.agents/`, `.claude/`
- **เหตุผล:** `ANN` บังคับ type hints, `S` (bandit) ช่วยจับปัญหา security, การปิด RUF001–003 กันไม่ให้ภาษาไทยถูกเตือนเรื่องอักขระคล้ายกัน และการยกเว้น `docs/` กันไม่ให้ ruff ไปแก้โค้ดตัวอย่างใน SPEC.md

## D-009 CI ตรึง GitHub Actions ด้วย commit SHA
- **บริบท:** `astral-sh/setup-uv` ไม่มี tag แบบ major (`v10`) ให้ใช้
- **ตัวเลือก:** (1) ตรึงด้วย tag เต็ม เช่น `v10.3.2` (2) ตรึงด้วย commit SHA พร้อม comment บอกเวอร์ชัน
- **เลือก:** (2) ทั้ง `actions/checkout` และ `setup-uv`
- **เหตุผล:** tag ย้ายไปชี้โค้ดอื่นได้ ส่วน SHA เปลี่ยนไม่ได้ (ป้องกัน supply chain) และอัปเดตด้วย Dependabot ได้ภายหลัง

## D-010 ย้าย `SPEC.md` ไปไว้ที่ `docs/SPEC.md`
*เจ้าของโปรเจกต์อนุมัติแล้ว*
- **บริบท:** ไฟล์อยู่ที่ root แต่ CLAUDE.md และสเปก section 4 อ้างถึง `docs/SPEC.md`
- **ตัวเลือก:** (1) ย้ายไฟล์ (2) คงไว้ที่เดิมแล้วแก้เอกสารที่อ้างถึง
- **เลือก:** (1)
- **เหตุผล:** เอกสารทุกฉบับอ้างถึง path เดียวกันอยู่แล้ว การย้ายไฟล์ที่เดียวจบกว่าการแก้หลายที่

## D-011 Windows + Smart App Control (เฉพาะเครื่องพัฒนา)
- **บริบท:** Smart App Control บล็อก `python.exe` ใน `.venv` ที่ uv สร้างจาก Python ที่ uv ดาวน์โหลดเอง (เป็น trampoline ที่ไม่มีลายเซ็น) และบล็อก `pytest.exe`/`uvicorn.exe` ที่ uv สร้างด้วย
- **ตัวเลือก:** (1) ปิด Smart App Control (เปิดคืนไม่ได้ถ้าไม่ reset Windows) (2) ใช้ WSL (3) ใช้ Python ที่มีลายเซ็น PSF แล้วรันเครื่องมือผ่าน `python -m`
- **เลือก:** (3)
  - ติดตั้ง Python ด้วย `py install 3.13`
  - สร้าง venv ด้วย `uv venv --python <path>`
  - รันเครื่องมือด้วย `uv run python -m pytest` และ `uv run python -m uvicorn ...`
  - `ruff` เป็น binary ที่รันได้ตามปกติ
- **เหตุผล:** ไม่ต้องลดระดับความปลอดภัยของเครื่อง และไม่มีผลกับ CI หรือ Vercel (Linux) คำสั่งใน CLAUDE.md ยังใช้ได้ตามเดิมบนเครื่องอื่น
