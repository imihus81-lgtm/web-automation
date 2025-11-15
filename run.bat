@echo off
IF NOT EXIST .venv\Scripts\activate (
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install
echo Example run:
echo python -m src.cli --niche "roofing contractor" --city "Dallas" --country "USA" --rows 60 --email
