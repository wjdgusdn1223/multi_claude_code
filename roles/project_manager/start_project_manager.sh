#!/bin/bash
cd "/home/jungh/workspace/web_community_test/roles/project_manager"

# 역할별 환경 설정
export ROLE_ID="project_manager"
export PROJECT_ROOT="/home/jungh/workspace/web_community_test"
export MASTER_HOST="localhost"
export MASTER_PORT="5000"

# Claude Code 실행 (예시 - 실제 환경에 맞게 수정 필요)
echo "Claude Code 역할 project_manager 시작"
echo "작업 디렉토리: /home/jungh/workspace/web_community_test/roles/project_manager"
echo "프롬프트 길이: $(echo '
# Project Manager 역할 수행

## 현재 상황
- 프로젝트: Web Community Platform
- 현재 단계: planning
- 작업 목표: ['프로젝트 목표 설정', '초기 계획 수립']

## 역할 설명
프로젝트 전체 관리 및 조율

## 현재 단계 컨텍스트
프로젝트 목표 설정, 초기 계획 수립, 리소스 계획

## 사용 가능한 도구들
### 언제 어떤 도구를 사용할지:
- **communication**: 다른 역할과 실시간 소통 (ActiveCommunicationEngine 사용)
- **timeline**: 타임라인 관리 (SimplifiedTimelineSystem 사용)
- **dashboard**: 대시보드 모니터링 (ProjectDashboardSystem 사용)

### 도구 사용 예시:
```python
# 다른 역할에게 질문
from enhanced_communication_system import ActiveCommunicationEngine
comm = ActiveCommunicationEngine(project_root)
response = comm.send_smart_message('backend_developer', 'API 스펙 확인 요청', MessageType.INFORMATION_REQUEST)
```


## 소통 방법
- 다른 역할과 소통이 필요하면 communication 시스템 사용
- 중요한 결정은 사용자 승인 요청
- 이전 단계로 되돌리기가 필요하면 rollback 요청

## 성공 기준
- 프로젝트 목표 설정
- 초기 계획 수립

## 주의사항
- 단계별로 충분한 품질 검증 필요
- 불확실한 부분은 즉시 소통
- 작업 진행 상황을 실시간 보고

이제 작업을 시작하세요.
' | wc -c) 문자"

# 프롬프트를 파일로 저장
cat > prompt.txt << 'EOF'

# Project Manager 역할 수행

## 현재 상황
- 프로젝트: Web Community Platform
- 현재 단계: planning
- 작업 목표: ['프로젝트 목표 설정', '초기 계획 수립']

## 역할 설명
프로젝트 전체 관리 및 조율

## 현재 단계 컨텍스트
프로젝트 목표 설정, 초기 계획 수립, 리소스 계획

## 사용자 메시지 모니터링
- user_message.txt 파일을 주기적으로 확인하여 사용자 메시지 처리
- 사용자 메시지가 있으면 response.txt 파일에 응답 작성
- 메시지 처리 후 user_message.txt 파일 삭제

## 사용 가능한 도구들
### 언제 어떤 도구를 사용할지:
- **communication**: 다른 역할과 실시간 소통 (ActiveCommunicationEngine 사용)
- **timeline**: 타임라인 관리 (SimplifiedTimelineSystem 사용)
- **dashboard**: 대시보드 모니터링 (ProjectDashboardSystem 사용)

### 도구 사용 예시:
```python
# 다른 역할에게 질문
from enhanced_communication_system import ActiveCommunicationEngine
comm = ActiveCommunicationEngine(project_root)
response = comm.send_smart_message('backend_developer', 'API 스펙 확인 요청', MessageType.INFORMATION_REQUEST)
```

## 메시지 처리 예시:
```python
import os
import time

# 사용자 메시지 확인
if os.path.exists('user_message.txt'):
    with open('user_message.txt', 'r', encoding='utf-8') as f:
        user_message = f.read()
    
    # 응답 생성
    response = f"프로젝트 매니저입니다. 메시지 내용: {user_message}에 대해 답변드리겠습니다."
    
    # 응답 파일 작성
    with open('response.txt', 'w', encoding='utf-8') as f:
        f.write(response)
    
    # 사용자 메시지 파일 삭제
    os.remove('user_message.txt')
```

## 소통 방법
- 다른 역할과 소통이 필요하면 communication 시스템 사용
- 중요한 결정은 사용자 승인 요청
- 이전 단계로 되돌리기가 필요하면 rollback 요청

## 성공 기준
- 프로젝트 목표 설정
- 초기 계획 수립

## 주의사항
- 단계별로 충분한 품질 검증 필요
- 불확실한 부분은 즉시 소통
- 작업 진행 상황을 실시간 보고
- 사용자 메시지를 주기적으로 확인하고 응답

이제 작업을 시작하세요.

EOF

# 실제 Claude Code 실행
echo "$(date): project_manager Claude Code 시작"

# 상태 파일 생성
echo "ACTIVE" > "/home/jungh/workspace/web_community_test/roles/project_manager/status.txt"

# 시그널 핸들러 설정
trap 'echo "$(date): project_manager 종료 신호 수신"; echo "STOPPED" > "/home/jungh/workspace/web_community_test/roles/project_manager/status.txt"; exit 0' SIGTERM SIGINT

# Claude Code 실행 (비대화형 모드)
claude-code --project="/home/jungh/workspace/web_community_test" --file="prompt.txt" --role="project_manager" --non-interactive 2>&1 | while read line; do
    echo "$(date): $line"
    echo "$(date): ACTIVE" > "/home/jungh/workspace/web_community_test/roles/project_manager/status.txt"
    
    # 종료 신호 확인
    if [ -f "/home/jungh/workspace/web_community_test/roles/project_manager/stop.signal" ]; then
        echo "$(date): project_manager 종료 신호 감지"
        echo "STOPPED" > "/home/jungh/workspace/web_community_test/roles/project_manager/status.txt"
        rm -f "/home/jungh/workspace/web_community_test/roles/project_manager/stop.signal"
        break
    fi
done

echo "$(date): project_manager 종료"
