# 🎯 Multi-Agent Claude Code System

완전 자율적인 소프트웨어 개발을 위한 멀티 에이전트 시스템입니다. 사용자가 "웹사이트 만들어줘"라고 하면 AI들이 기획부터 배포까지 자동으로 처리합니다.

## 🚀 주요 특징

### 1. **마스터 오케스트레이터**
- 모든 AI 역할들을 중앙에서 관리
- Claude Code 인스턴스 자동 실행/종료
- 실시간 상태 모니터링 및 제어

### 2. **7개 전문 역할**
- **Project Manager**: 프로젝트 전체 관리
- **Business Analyst**: 비즈니스 요구사항 분석
- **System Architect**: 시스템 설계 및 아키텍처
- **Frontend Developer**: 프론트엔드 개발
- **Backend Developer**: 백엔드 개발
- **QA Tester**: 품질 보증 및 테스트
- **DevOps Engineer**: 배포 및 운영

### 3. **스마트 워크플로우**
```
Planning → Requirements → Design → Development → Testing → Deployment
```

### 4. **실시간 소통 시스템**
- 역할 간 자동 소통 (작업 중에도!)
- 이전 단계 롤백 시스템
- 사용자 승인 요청 처리

### 5. **통합 웹 UI**
- 실시간 대시보드
- 관리 콘솔
- 파일 탐색기
- 사용자 결정 인터페이스

## 🛠️ 시스템 구성

### 핵심 시스템들
- `master_orchestrator.py`: 마스터 제어 시스템
- `enhanced_communication_system.py`: 역할 간 소통
- `intelligent_review_system.py`: 품질 리뷰
- `context_persistence_system.py`: 학습 및 기억
- `smart_file_discovery_system.py`: 파일 탐색
- `document_tracking_system.py`: 문서 추적
- `modular_document_templates.py`: 모듈화된 문서
- `ai_optimized_deliverable_templates.py`: AI 전용 산출물
- `seamless_role_transition_system.py`: 역할 전환
- `autonomous_workflow_orchestrator.py`: 자율 워크플로우
- `simplified_timeline_system.py`: 타임라인 관리
- `project_dashboard_system.py`: 프로젝트 대시보드

## 🏁 빠른 시작

### 1. 시스템 시작
```bash
# 마스터 오케스트레이터 실행
python master_orchestrator.py
```

### 2. 웹 UI 접속
```
http://localhost:5000
```

### 3. 프로젝트 시작
웹 UI에서 새 프로젝트를 시작하거나, 코드에서 직접 시작:

```python
from master_orchestrator import MasterOrchestrator

# 마스터 오케스트레이터 초기화
orchestrator = MasterOrchestrator("/path/to/project")

# 프로젝트 설정
project_config = {
    "name": "My Web Project",
    "description": "웹 커뮤니티 플랫폼",
    "features": ["사용자 인증", "게시판", "댓글 시스템"],
    "tech_stack": {
        "frontend": "React",
        "backend": "Node.js", 
        "database": "PostgreSQL"
    }
}

# 프로젝트 시작 (이후 모든 것이 자동!)
orchestrator.start_project(project_config)
```

## 🎮 사용 방법

### 1. **자동 진행 모드**
- 프로젝트 시작 후 AI들이 자동으로 작업
- 각 단계별로 자동 전환
- 필요시에만 사용자 승인 요청

### 2. **실시간 모니터링**
- 웹 UI에서 모든 역할 상태 확인
- 실시간 진행률 및 알림
- 산출물 및 레포트 확인

### 3. **사용자 개입**
- 중요한 결정 시 승인 요청
- 롤백 요청 처리
- 수동 역할 제어 가능

### 4. **파일 및 산출물 관리**
- 실시간 파일 탐색
- 자동 문서 생성
- 품질 추적 및 리뷰

## 🔧 고급 기능

### 1. **롤백 시스템**
```python
# QA가 설계 문제 발견 시
qa_tester: "아키텍처 문제 발견"
→ 자동으로 설계 단계로 롤백
→ 수정 후 다시 진행
```

### 2. **실시간 소통**
```python
# 개발 중 실시간 소통
frontend_dev: "API 스펙이 모호함"
→ 즉시 backend_dev와 소통
→ 스펙 명확화 후 작업 계속
```

### 3. **지능적 품질 관리**
- AI-to-AI 자동 리뷰
- 품질 점수 기반 승인
- 자동 테스트 및 검증

### 4. **학습 및 적응**
- 프로젝트 경험 학습
- 패턴 인식 및 개선
- 점진적 성능 향상

## 📊 대시보드 기능

### 1. **실시간 상태**
- 현재 프로젝트 단계
- 활성 역할 수
- 대기 중인 작업
- 알림 및 경고

### 2. **역할 관리**
- 각 역할 상태 모니터링
- 수동 시작/중지 제어
- 성능 지표 확인
- 작업 진행률

### 3. **사용자 결정**
- 승인 요청 처리
- 옵션 선택 인터페이스
- 결정 이력 추적

### 4. **파일 탐색**
- 프로젝트 파일 구조
- 산출물 다운로드
- 문서 및 레포트 확인

## 🎯 사용 시나리오

### 시나리오 1: 웹사이트 개발
```
1. 사용자: "커뮤니티 웹사이트 만들어줘"
2. Business Analyst: 요구사항 분석 시작
3. System Architect: 아키텍처 설계
4. Developers: 프론트엔드/백엔드 개발
5. QA Tester: 품질 검증
6. DevOps: 배포 및 운영
```

### 시나리오 2: 품질 이슈 발견
```
1. QA가 설계 문제 발견
2. 자동으로 설계 단계 롤백 요청
3. 사용자 승인 후 롤백 실행
4. Architect가 설계 수정
5. 다시 개발 단계 진행
```

### 시나리오 3: 실시간 소통
```
1. Frontend Dev: "API 응답 형식이 불분명"
2. 즉시 Backend Dev와 소통
3. API 스펙 명확화
4. 작업 계속 진행
```

## 🔒 보안 및 품질

### 1. **자동 품질 검증**
- 코드 리뷰 자동화
- 테스트 커버리지 확인
- 보안 스캔 실행

### 2. **사용자 제어**
- 중요 결정 승인 시스템
- 수동 개입 가능
- 안전한 롤백 기능

### 3. **데이터 보안**
- 로컬 파일 시스템 사용
- 외부 전송 최소화
- 접근 권한 관리

## 📝 로그 및 추적

### 1. **상세 로깅**
- 모든 역할 활동 기록
- 결정 과정 추적
- 오류 및 예외 로그

### 2. **성능 메트릭**
- 역할별 성능 점수
- 작업 완료 시간
- 품질 지표 추적

### 3. **프로젝트 이력**
- 워크플로우 진행 기록
- 사용자 결정 이력
- 롤백 및 수정 사항

## 🛟 문제 해결

### 일반적인 문제

**Q: 역할이 시작되지 않음**
- 작업 디렉토리 권한 확인
- 로그 파일 확인
- 프로세스 상태 점검

**Q: 웹 UI 접속 불가**
- 포트 5000 사용 가능 여부 확인
- 방화벽 설정 확인
- 브라우저 캐시 삭제

**Q: 프로젝트 진행 중단**
- 마스터 오케스트레이터 상태 확인
- 역할 간 소통 로그 확인
- 사용자 결정 대기 여부 확인

### 디버깅 팁

1. **로그 확인**
   ```bash
   tail -f master_orchestrator/logs/master.log
   ```

2. **데이터베이스 확인**
   ```bash
   sqlite3 master_orchestrator/orchestrator.db
   ```

3. **프로세스 상태 확인**
   ```bash
   ps aux | grep python
   ```

## 🔄 업데이트 및 확장

### 새 역할 추가
```python
# available_roles에 새 역할 정의
"new_role": {
    "name": "New Role",
    "description": "새로운 역할 설명",
    "tools": ["사용할 도구들"],
    "decision_authority": "권한 수준"
}
```

### 새 워크플로우 단계
```python
# workflow_steps에 새 단계 추가
WorkflowStep(
    step_id="새_단계_ID",
    phase=새_단계_ENUM,
    roles_required=["필요한_역할들"],
    dependencies=["의존성_단계들"]
)
```

## 📞 지원 및 문의

이 시스템은 Claude Code와 함께 사용하도록 설계되었습니다. 

### 주요 의존성
- Python 3.8+
- Flask, Flask-SocketIO
- SQLite3
- 기타 requirements.txt 참조

### 개발 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python -c "from master_orchestrator import MasterOrchestrator; MasterOrchestrator('.')"
```

---

**🎯 이제 "웹사이트 만들어줘"라고 말하면 AI들이 알아서 완성합니다!**