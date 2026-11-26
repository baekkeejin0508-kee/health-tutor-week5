"""Student access codes and classroom aliases."""

import hashlib
import re
import secrets
from datetime import datetime
from collections.abc import Mapping


MAX_CODES_PER_CLASS = 20
FLOWER_ALIASES = tuple("""
백합 장미 튤립 프리지아 수선화 국화 안개꽃 해바라기 라벤더 카네이션
동백 민들레 진달래 개나리 목련 벚꽃 철쭉 매화 봉선화 해란초
수국 작약 모란 코스모스 채송화 나팔꽃 무궁화 달맞이꽃 금잔화 금어초
제비꽃 양귀비 맨드라미 접시꽃 히아신스 라일락 물망초 은방울꽃 패랭이꽃 과꽃
소국 여우꼬리꽃 팬지 거베라 데이지 마거리트 루피너스 글라디올러스 리시안셔스 스톡
스위트피 알리움 클레마티스 아네모네 라넌큘러스 베고니아 제라늄 페튜니아 메리골드 봉래화
꽃잔디 뻐꾹나리 하늘나리 참나리 등꽃 능소화 꽃창포 아이리스 도라지 초롱꽃
자란 풍란 춘란 보춘화 석곡 에델바이스 구절초 벌개미취 쑥부쟁이 샤스타데이지
큰금계국 금낭화 꽃양귀비 금불초 황매화 괭이밥 할미꽃 산수유 배롱나무꽃 복수초
옥잠화 비비추 설강화 크로커스 용담 산철쭉 치자꽃 백일홍 연꽃 수련
""".split())
CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_PATTERN = re.compile(f"[{CODE_ALPHABET}]{{20}}")
TEAM_NAMES = (
    "햇살", "구름", "바람", "별빛", "무지개", "파도", "노을", "이슬", "은하", "새벽",
    "나무", "바다", "숲길", "달빛", "하늘", "샘물", "물결", "들판", "산들", "눈송이",
    *(f"{number}모둠" for number in range(1, 31)),
)


def distribution_mark(uid: str) -> str:
    """A teacher-only label independent of student order and login credentials."""
    digest = hashlib.sha256(f"distribution:{uid}".encode("utf-8")).hexdigest()[:10].upper()
    return f"HQ-{digest[:5]}-{digest[5:]}"


def record_uses_access_code(record: Mapping) -> bool:
    """Recognize both new private-profile markers and older stored records."""
    return record.get("login_method") == "access_code" or bool(record.get("access_number"))


def generate_access_code() -> str:
    raw = "".join(secrets.choice(CODE_ALPHABET) for _ in range(20))
    return "-".join(raw[start:start + 5] for start in range(0, 20, 5))


def code_digest(code: str) -> str:
    normalized = re.sub(r"[\s-]", "", code).upper()
    if not CODE_PATTERN.fullmatch(normalized):
        return ""
    return hashlib.sha256(normalized.encode("ascii")).hexdigest()


def access_expiration(issued_at: datetime) -> datetime:
    try:
        return issued_at.replace(year=issued_at.year + 3)
    except ValueError:
        return issued_at.replace(year=issued_at.year + 3, day=28)
