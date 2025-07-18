#!/bin/bash

# Multi-Claude Code System Setup Script
# This script initializes the role-based development environment

echo "Setting up Multi-Claude Code System..."

# Function to create status.yaml for each role
create_role_status() {
    local role_id=$1
    local role_name=$2
    local status_file="roles/${role_id}/status.yaml"
    
    # Copy template and customize
    cp status_template.yaml "$status_file"
    
    # Update role-specific information
    sed -i "s/role_name: \"\"/role_name: \"${role_name}\"/" "$status_file"
    sed -i "s/role_id: \"\"/role_id: \"${role_id}\"/" "$status_file"
    sed -i "s/start_date: \"\"/start_date: \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"/" "$status_file"
    sed -i "s/last_updated: \"\"/last_updated: \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"/" "$status_file"
    sed -i "s/phase: \"\"/phase: \"planning\"/" "$status_file"
    
    echo "Created status file for ${role_name} (${role_id})"
}

# Read roles from roles.yaml and create status files
echo "Creating individual status files for each role..."

# Create status files for all roles
create_role_status "project_manager" "Project Manager"
create_role_status "product_owner" "Product Owner"
create_role_status "business_analyst" "Business Analyst"
create_role_status "requirements_analyst" "Requirements Analyst"
create_role_status "ux_researcher" "UX Researcher"
create_role_status "system_architect" "System Architect"
create_role_status "solution_architect" "Solution Architect"
create_role_status "ui_ux_designer" "UI/UX Designer"
create_role_status "database_designer" "Database Designer"
create_role_status "frontend_developer" "Frontend Developer"
create_role_status "backend_developer" "Backend Developer"
create_role_status "fullstack_developer" "Fullstack Developer"
create_role_status "mobile_developer" "Mobile Developer"
create_role_status "devops_engineer" "DevOps Engineer"
create_role_status "qa_tester" "QA Tester"
create_role_status "automation_tester" "Automation Tester"
create_role_status "performance_tester" "Performance Tester"
create_role_status "security_tester" "Security Tester"
create_role_status "infrastructure_engineer" "Infrastructure Engineer"
create_role_status "cloud_engineer" "Cloud Engineer"
create_role_status "sre_engineer" "Site Reliability Engineer"
create_role_status "monitoring_engineer" "Monitoring Engineer"
create_role_status "technical_reviewer" "Technical Reviewer"
create_role_status "senior_developer" "Senior Developer"
create_role_status "project_owner" "Project Owner"
create_role_status "stakeholder" "Stakeholder"
create_role_status "end_user" "End User"
create_role_status "beta_tester" "Beta Tester"
create_role_status "user_support" "User Support"

# Create common directories
echo "Creating common directories..."
mkdir -p {shared,deliverables,documentation,artifacts,logs}

# Create shared workspace directories
mkdir -p shared/{requirements,designs,code,tests,configs,docs}

# Create deliverables directories
mkdir -p deliverables/{planning,development,testing,deployment,maintenance}

# Create initial project configuration
echo "Creating project configuration..."
cat > project_config.yaml << 'EOF'
project:
  name: "Multi-Claude Code Sample Project"
  description: "A sample project demonstrating multi-Claude Code collaboration"
  start_date: ""
  target_completion: ""
  priority: "medium"
  status: "initiation"

team:
  size: 29
  active_roles: []
  master_role: "project_manager"

phases:
  current: "initiation"
  completed: []
  upcoming: ["planning", "execution", "monitoring", "closure"]

settings:
  auto_assignment: true
  dependency_checking: true
  status_synchronization: true
  notification_system: true
EOF

# Update project start date
sed -i "s/start_date: \"\"/start_date: \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"/" project_config.yaml

# Create README for the system
echo "Creating system README..."
cat > README.md << 'EOF'
# Multi-Claude Code System

이 시스템은 복수의 Claude Code 인스턴스가 협업하여 하나의 프로젝트를 개발하는 환경을 제공합니다.

## 구조

```
multi_claude_code_sample/
├── roles/                  # 각 역할별 디렉토리
│   ├── project_manager/
│   ├── frontend_developer/
│   ├── backend_developer/
│   └── ...
├── shared/                 # 공유 작업 공간
├── deliverables/           # 산출물 저장소
├── documentation/          # 문서 저장소
├── roles.yaml             # 역할 정의
├── automation_rules.yaml  # 자동화 룰
├── status_template.yaml   # 상태 템플릿
└── project_config.yaml    # 프로젝트 설정
```

## 사용법

1. 각 역할의 Claude Code는 해당 역할 디렉토리에서 실행
2. `status.yaml` 파일을 통해 현재 상태 추적
3. `automation_rules.yaml`에 따라 자동화 동작 수행
4. 의존성 관리 및 협업 자동화

## 역할별 시작 방법

각 역할의 Claude Code 시작 시:
```bash
cd roles/{role_name}
claude-code
```

역할별 상태 파일 확인:
```bash
cat roles/{role_name}/status.yaml
```
EOF

# Make Python scripts executable
chmod +x master_controller.py
chmod +x role_bootstrap.py

# Create startup scripts for each role
echo "Creating role startup scripts..."
for role_dir in roles/*/; do
    if [ -d "$role_dir" ]; then
        role_name=$(basename "$role_dir")
        cat > "${role_dir}/start_role.sh" << 'EOFSCRIPT'
#!/bin/bash
echo "Starting role initialization..."
python3 ../../role_bootstrap.py
echo "Role environment ready. Starting Claude Code..."
claude-code --resume
EOFSCRIPT
        chmod +x "${role_dir}/start_role.sh"
    fi
done

echo "Setup completed successfully!"
echo ""
echo "🚀 사용 방법:"
echo "1. 마스터 컨트롤러 시작: python3 master_controller.py --status"
echo "2. 특정 역할 시작: python3 master_controller.py --start-role project_manager"
echo "3. 또는 직접 역할 디렉토리에서: cd roles/project_manager && ./start_role.sh"
echo ""
echo "🎯 추천 시작 순서:"
echo "1. cd roles/project_manager && ./start_role.sh"
echo "2. 다른 터미널에서 마스터 모니터링: python3 master_controller.py --status"