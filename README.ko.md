# Medicine Agent — 분자 후보 평가 에이전트

기존의 RDKit·ADMET-AI 등 분자 평가 도구를 조합해 **동일한 예산에서 후보 평가 정책을 비교**하는 연구·교육용 프로젝트입니다. 실제 약효, 독성 안전성 또는 합성 성공을 입증하는 소프트웨어가 아닙니다.

## 구현 현황

- RDKit: SMILES 유효성·정규화·중복 제거, QED·분자량·cLogP·TPSA·SA Score, Morgan Fingerprint
- 예산·도구 권한 검사, Pareto/구조 다양성, `fixed/rules/agent` 오프라인 평가
- SQLite 점수 캐시, 실행 결과 CSV/JSON, 비교 CLI, Streamlit 결과 화면, 중단·재개
- 선택형 ADMET-AI 어댑터 및 Strands 에이전트 도구, TxGemma Predict 출력 파서
- ChEMBL 공개 API에서 고유 유효 SMILES **120개를 실제 수집**한 자동화 검증과 3정책×3시드 모의 벤치마크

**검증 경계:** 기본 `agent`는 실제 LLM이 아닌 결정적 모의 정책이고 `fixture_risk`는 합성 점수입니다. 실제 ADMET-AI 모델 가중치 및 실제 LLM을 함께 실행한 결과나 모델 예측 정확도를 의미하지 않습니다.

## 설치 및 재현

Python 3.11 환경:

```bash
python -m pip install -e '.[test,ui]'
pytest -q
amo prepare --input data/fixtures/smiles.csv --output /tmp/amo-prepared.csv
amo compare --input /tmp/amo-prepared.csv --budget 3 --seeds 42 43 44 --out outputs/compare
amo ui --runs outputs/compare
```

선택형 실제 공개 데이터 수집:

```bash
python scripts/fetch_chembl_pool.py --count 120 --out data/processed/chembl_pool.csv
```

검증 단계 및 미완료 사항은 [품질 게이트](docs/QUALITY_GATES.md), [로드맵](docs/ROADMAP.md), [ADMET 실행](docs/ADMET_SMOKE.md), [LLM 실행](docs/AGENT_LIVE.md)을 참고하세요.

이 저장소의 채팅 기반 개발 지침은 기존 [AGENTS.md](AGENTS.md) 및 [.agents 스킬](.agents/skills/luna-chat-coder/SKILL.md)에 보존되어 있습니다.
