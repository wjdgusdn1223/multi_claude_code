#!/usr/bin/env python3
"""
Project Dashboard System for Multi-Agent Claude Code
실시간 프로젝트 대시보드 UI 시스템
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import time
import sqlite3
from flask import Flask, render_template, jsonify, request
import socketio
from flask_socketio import SocketIO, emit

class DashboardMetricType(Enum):
    """대시보드 메트릭 타입"""
    PROGRESS = "progress"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    COMMUNICATION = "communication"
    ERRORS = "errors"
    RESOURCE_USAGE = "resource_usage"
    TIMELINE = "timeline"

class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class DashboardMetric:
    """대시보드 메트릭"""
    metric_id: str
    metric_type: DashboardMetricType
    name: str
    value: Union[int, float, str]
    unit: str
    trend: str  # "up", "down", "stable"
    target_value: Optional[Union[int, float]]
    timestamp: datetime
    role_id: Optional[str]
    project_phase: Optional[str]

@dataclass
class DashboardAlert:
    """대시보드 알림"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool
    action_required: bool
    related_metrics: List[str]

@dataclass
class RoleStatus:
    """역할 상태"""
    role_id: str
    role_name: str
    status: str  # "active", "idle", "busy", "error"
    current_task: Optional[str]
    progress_percentage: float
    last_activity: datetime
    performance_score: float
    tasks_completed: int
    tasks_pending: int
    average_task_time: float

class ProjectDashboardSystem:
    """프로젝트 대시보드 시스템"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dashboard_dir = self.project_root / "dashboard"
        self.data_dir = self.dashboard_dir / "data"
        self.templates_dir = self.dashboard_dir / "templates"
        self.static_dir = self.dashboard_dir / "static"
        
        # 디렉토리 생성
        self.dashboard_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.static_dir.mkdir(exist_ok=True)
        
        # 데이터베이스 초기화
        self.db_path = self.data_dir / "dashboard.db"
        self._init_database()
        
        # Flask 앱 및 SocketIO 설정
        self.app = Flask(__name__, 
                        template_folder=str(self.templates_dir),
                        static_folder=str(self.static_dir))
        self.app.config['SECRET_KEY'] = 'dashboard_secret_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # 실시간 데이터 수집
        self.metrics_cache: Dict[str, DashboardMetric] = {}
        self.alerts_cache: Dict[str, DashboardAlert] = {}
        self.role_status_cache: Dict[str, RoleStatus] = {}
        self.cache_lock = threading.Lock()
        
        # 데이터 수집 스레드
        self.data_collection_active = True
        self.data_thread = threading.Thread(target=self._collect_data_loop, daemon=True)
        
        # 웹 라우트 설정
        self._setup_routes()
        
        # 기본 UI 파일 생성
        self._create_dashboard_templates()
        self._create_dashboard_assets()
        
        print("📊 Project Dashboard System 초기화 완료")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS dashboard_metrics (
                    metric_id TEXT PRIMARY KEY,
                    metric_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    trend TEXT NOT NULL,
                    target_value TEXT,
                    timestamp TEXT NOT NULL,
                    role_id TEXT,
                    project_phase TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS dashboard_alerts (
                    alert_id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    action_required BOOLEAN DEFAULT FALSE,
                    related_metrics TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS role_status (
                    role_id TEXT PRIMARY KEY,
                    role_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_task TEXT,
                    progress_percentage REAL NOT NULL,
                    last_activity TEXT NOT NULL,
                    performance_score REAL NOT NULL,
                    tasks_completed INTEGER DEFAULT 0,
                    tasks_pending INTEGER DEFAULT 0,
                    average_task_time REAL DEFAULT 0.0,
                    updated_at TEXT NOT NULL
                )
            ''')
    
    def _setup_routes(self):
        """웹 라우트 설정"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/overview')
        def get_overview():
            return jsonify(self._get_project_overview())
        
        @self.app.route('/api/metrics')
        def get_metrics():
            metric_type = request.args.get('type')
            return jsonify(self._get_metrics(metric_type))
        
        @self.app.route('/api/alerts')
        def get_alerts():
            level = request.args.get('level')
            return jsonify(self._get_alerts(level))
        
        @self.app.route('/api/roles')
        def get_roles():
            return jsonify(self._get_role_statuses())
        
        @self.app.route('/api/timeline')
        def get_timeline():
            days = int(request.args.get('days', 7))
            return jsonify(self._get_timeline_data(days))
        
        @self.socketio.on('connect')
        def handle_connect():
            print('클라이언트 연결됨')
            emit('connected', {'status': 'success'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('클라이언트 연결 해제됨')
        
        @self.socketio.on('request_update')
        def handle_update_request():
            self._emit_real_time_data()
    
    def _create_dashboard_templates(self):
        """대시보드 템플릿 파일 생성"""
        
        # 메인 대시보드 HTML
        dashboard_html = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Agent Project Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='dashboard.css') }}">
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- 헤더 -->
    <header class="bg-white shadow-lg border-b">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <i class="fas fa-robot text-blue-600 text-2xl mr-3"></i>
                    <h1 class="text-2xl font-bold text-gray-800">Multi-Agent Project Dashboard</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <div id="connection-status" class="flex items-center">
                        <div class="w-3 h-3 bg-green-500 rounded-full mr-2 pulse"></div>
                        <span class="text-sm text-gray-600">실시간 연결</span>
                    </div>
                    <div class="text-sm text-gray-500" id="last-update">
                        마지막 업데이트: --
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- 메인 대시보드 -->
    <main class="container mx-auto px-6 py-8">
        <!-- 프로젝트 개요 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
                <div class="flex items-center">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-700">전체 진행률</h3>
                        <p class="text-3xl font-bold text-blue-600" id="overall-progress">--</p>
                    </div>
                    <i class="fas fa-chart-line text-blue-500 text-2xl"></i>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
                <div class="flex items-center">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-700">활성 역할</h3>
                        <p class="text-3xl font-bold text-green-600" id="active-roles">--</p>
                    </div>
                    <i class="fas fa-users text-green-500 text-2xl"></i>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
                <div class="flex items-center">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-700">대기 중 작업</h3>
                        <p class="text-3xl font-bold text-yellow-600" id="pending-tasks">--</p>
                    </div>
                    <i class="fas fa-clock text-yellow-500 text-2xl"></i>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
                <div class="flex items-center">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-700">알림</h3>
                        <p class="text-3xl font-bold text-red-600" id="alert-count">--</p>
                    </div>
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl"></i>
                </div>
            </div>
        </div>

        <!-- 메인 콘텐츠 -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- 역할 상태 -->
            <div class="lg:col-span-2">
                <div class="bg-white rounded-lg shadow overflow-hidden">
                    <div class="px-6 py-4 bg-gray-50 border-b">
                        <h2 class="text-xl font-semibold text-gray-800">
                            <i class="fas fa-user-cog mr-2"></i>역할 상태
                        </h2>
                    </div>
                    <div class="p-6">
                        <div id="roles-container" class="space-y-4">
                            <!-- 역할 카드들이 여기에 동적으로 추가됩니다 -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- 실시간 알림 -->
            <div>
                <div class="bg-white rounded-lg shadow overflow-hidden">
                    <div class="px-6 py-4 bg-gray-50 border-b">
                        <h2 class="text-xl font-semibold text-gray-800">
                            <i class="fas fa-bell mr-2"></i>실시간 알림
                        </h2>
                    </div>
                    <div class="p-6">
                        <div id="alerts-container" class="space-y-3 max-h-96 overflow-y-auto">
                            <!-- 알림들이 여기에 동적으로 추가됩니다 -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 성능 차트 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
            <div class="bg-white rounded-lg shadow">
                <div class="px-6 py-4 bg-gray-50 border-b">
                    <h2 class="text-xl font-semibold text-gray-800">
                        <i class="fas fa-chart-area mr-2"></i>진행률 추이
                    </h2>
                </div>
                <div class="p-6">
                    <canvas id="progress-chart" height="300"></canvas>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow">
                <div class="px-6 py-4 bg-gray-50 border-b">
                    <h2 class="text-xl font-semibold text-gray-800">
                        <i class="fas fa-tachometer-alt mr-2"></i>성능 지표
                    </h2>
                </div>
                <div class="p-6">
                    <canvas id="performance-chart" height="300"></canvas>
                </div>
            </div>
        </div>

        <!-- 작업 타임라인 -->
        <div class="bg-white rounded-lg shadow mt-8">
            <div class="px-6 py-4 bg-gray-50 border-b">
                <h2 class="text-xl font-semibold text-gray-800">
                    <i class="fas fa-timeline mr-2"></i>작업 타임라인
                </h2>
            </div>
            <div class="p-6">
                <div id="timeline-container" class="timeline">
                    <!-- 타임라인 이벤트들이 여기에 동적으로 추가됩니다 -->
                </div>
            </div>
        </div>
    </main>

    <script src="{{ url_for('static', filename='dashboard.js') }}"></script>
</body>
</html>'''
        
        with open(self.templates_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
    
    def _create_dashboard_assets(self):
        """대시보드 CSS/JS 파일 생성"""
        
        # CSS 파일
        dashboard_css = '''
.pulse {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.role-card {
    transition: all 0.3s ease;
}

.role-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.status-active { @apply bg-green-100 text-green-800; }
.status-busy { @apply bg-yellow-100 text-yellow-800; }
.status-idle { @apply bg-gray-100 text-gray-800; }
.status-error { @apply bg-red-100 text-red-800; }

.alert-info { @apply border-l-4 border-blue-500 bg-blue-50; }
.alert-warning { @apply border-l-4 border-yellow-500 bg-yellow-50; }
.alert-error { @apply border-l-4 border-red-500 bg-red-50; }
.alert-critical { @apply border-l-4 border-purple-500 bg-purple-50; }

.timeline {
    position: relative;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 30px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e5e7eb;
}

.timeline-item {
    position: relative;
    padding-left: 60px;
    margin-bottom: 24px;
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: 24px;
    top: 6px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #3b82f6;
    border: 3px solid white;
    box-shadow: 0 0 0 2px #e5e7eb;
}

.progress-bar {
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3b82f6, #1d4ed8);
    border-radius: 4px;
    transition: width 0.3s ease;
}
'''
        
        with open(self.static_dir / 'dashboard.css', 'w', encoding='utf-8') as f:
            f.write(dashboard_css)
        
        # JavaScript 파일
        dashboard_js = '''
class DashboardManager {
    constructor() {
        this.socket = io();
        this.charts = {};
        this.initializeSocketListeners();
        this.initializeCharts();
        this.loadInitialData();
    }

    initializeSocketListeners() {
        this.socket.on('connect', () => {
            console.log('서버에 연결됨');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('서버 연결 해제됨');
            this.updateConnectionStatus(false);
        });

        this.socket.on('dashboard_update', (data) => {
            this.updateDashboard(data);
        });

        this.socket.on('new_alert', (alert) => {
            this.addAlert(alert);
        });

        this.socket.on('role_update', (roleData) => {
            this.updateRoleStatus(roleData);
        });
    }

    initializeCharts() {
        // 진행률 차트
        const progressCtx = document.getElementById('progress-chart').getContext('2d');
        this.charts.progress = new Chart(progressCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '전체 진행률',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        // 성능 차트
        const performanceCtx = document.getElementById('performance-chart').getContext('2d');
        this.charts.performance = new Chart(performanceCtx, {
            type: 'doughnut',
            data: {
                labels: ['완료', '진행 중', '대기'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    async loadInitialData() {
        try {
            // 개요 데이터 로드
            const overview = await fetch('/api/overview').then(r => r.json());
            this.updateOverview(overview);

            // 역할 상태 로드
            const roles = await fetch('/api/roles').then(r => r.json());
            this.updateRoles(roles);

            // 알림 로드
            const alerts = await fetch('/api/alerts').then(r => r.json());
            this.updateAlerts(alerts);

            // 타임라인 로드
            const timeline = await fetch('/api/timeline').then(r => r.json());
            this.updateTimeline(timeline);

        } catch (error) {
            console.error('초기 데이터 로드 실패:', error);
        }
    }

    updateConnectionStatus(connected) {
        const status = document.getElementById('connection-status');
        const indicator = status.querySelector('div');
        const text = status.querySelector('span');

        if (connected) {
            indicator.className = 'w-3 h-3 bg-green-500 rounded-full mr-2 pulse';
            text.textContent = '실시간 연결';
        } else {
            indicator.className = 'w-3 h-3 bg-red-500 rounded-full mr-2';
            text.textContent = '연결 끊김';
        }
    }

    updateOverview(data) {
        document.getElementById('overall-progress').textContent = data.overall_progress + '%';
        document.getElementById('active-roles').textContent = data.active_roles;
        document.getElementById('pending-tasks').textContent = data.pending_tasks;
        document.getElementById('alert-count').textContent = data.alert_count;
    }

    updateRoles(roles) {
        const container = document.getElementById('roles-container');
        container.innerHTML = '';

        roles.forEach(role => {
            const roleCard = this.createRoleCard(role);
            container.appendChild(roleCard);
        });
    }

    createRoleCard(role) {
        const card = document.createElement('div');
        card.className = 'role-card bg-gray-50 rounded-lg p-4 border';
        
        card.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                        ${role.role_name.charAt(0).toUpperCase()}
                    </div>
                    <div class="ml-3">
                        <h3 class="font-semibold text-gray-800">${role.role_name}</h3>
                        <p class="text-sm text-gray-600">${role.role_id}</p>
                    </div>
                </div>
                <span class="px-3 py-1 rounded-full text-xs font-medium status-${role.status}">
                    ${this.getStatusText(role.status)}
                </span>
            </div>
            
            <div class="mb-3">
                <div class="flex justify-between text-sm text-gray-600 mb-1">
                    <span>진행률</span>
                    <span>${role.progress_percentage}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${role.progress_percentage}%"></div>
                </div>
            </div>
            
            <div class="text-sm text-gray-600">
                <p><strong>현재 작업:</strong> ${role.current_task || '없음'}</p>
                <p><strong>완료:</strong> ${role.tasks_completed}개 | <strong>대기:</strong> ${role.tasks_pending}개</p>
                <p><strong>성능 점수:</strong> ${role.performance_score.toFixed(2)}</p>
            </div>
        `;
        
        return card;
    }

    getStatusText(status) {
        const statusMap = {
            'active': '활성',
            'busy': '작업 중',
            'idle': '대기',
            'error': '오류'
        };
        return statusMap[status] || status;
    }

    updateAlerts(alerts) {
        const container = document.getElementById('alerts-container');
        container.innerHTML = '';

        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center">새로운 알림이 없습니다.</p>';
            return;
        }

        alerts.forEach(alert => {
            const alertElement = this.createAlertElement(alert);
            container.appendChild(alertElement);
        });
    }

    createAlertElement(alert) {
        const element = document.createElement('div');
        element.className = `alert-${alert.level} p-3 rounded border`;
        
        element.innerHTML = `
            <div class="flex items-start">
                <i class="fas fa-${this.getAlertIcon(alert.level)} mt-1 mr-2"></i>
                <div class="flex-1">
                    <h4 class="font-semibold text-sm">${alert.title}</h4>
                    <p class="text-xs text-gray-600 mt-1">${alert.message}</p>
                    <p class="text-xs text-gray-500 mt-1">${this.formatTime(alert.timestamp)}</p>
                </div>
            </div>
        `;
        
        return element;
    }

    getAlertIcon(level) {
        const iconMap = {
            'info': 'info-circle',
            'warning': 'exclamation-triangle',
            'error': 'times-circle',
            'critical': 'skull'
        };
        return iconMap[level] || 'info-circle';
    }

    updateTimeline(timelineData) {
        const container = document.getElementById('timeline-container');
        container.innerHTML = '';

        timelineData.forEach(event => {
            const timelineItem = this.createTimelineItem(event);
            container.appendChild(timelineItem);
        });
    }

    createTimelineItem(event) {
        const item = document.createElement('div');
        item.className = 'timeline-item';
        
        item.innerHTML = `
            <div class="bg-white rounded border p-3">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-sm">${event.title}</h4>
                    <span class="text-xs text-gray-500">${this.formatTime(event.timestamp)}</span>
                </div>
                <p class="text-sm text-gray-600">${event.description}</p>
                ${event.role ? `<span class="text-xs text-blue-600 mt-1 inline-block">${event.role}</span>` : ''}
            </div>
        `;
        
        return item;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('ko-KR');
    }

    updateDashboard(data) {
        if (data.overview) this.updateOverview(data.overview);
        if (data.roles) this.updateRoles(data.roles);
        if (data.alerts) this.updateAlerts(data.alerts);
        
        document.getElementById('last-update').textContent = 
            `마지막 업데이트: ${new Date().toLocaleTimeString('ko-KR')}`;
    }

    addAlert(alert) {
        // 새 알림을 맨 위에 추가
        const container = document.getElementById('alerts-container');
        const alertElement = this.createAlertElement(alert);
        container.insertBefore(alertElement, container.firstChild);
        
        // 알림 수 업데이트
        const alertCount = document.getElementById('alert-count');
        alertCount.textContent = parseInt(alertCount.textContent) + 1;
    }

    updateRoleStatus(roleData) {
        // 특정 역할의 상태만 업데이트
        this.loadInitialData(); // 간단한 구현으로 전체 새로고침
    }
}

// 대시보드 초기화
document.addEventListener('DOMContentLoaded', () => {
    new DashboardManager();
});

// 주기적 업데이트 요청
setInterval(() => {
    if (window.dashboard && window.dashboard.socket.connected) {
        window.dashboard.socket.emit('request_update');
    }
}, 30000); // 30초마다
'''
        
        with open(self.static_dir / 'dashboard.js', 'w', encoding='utf-8') as f:
            f.write(dashboard_js)
    
    def start_dashboard_server(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """대시보드 서버 시작"""
        
        # 데이터 수집 스레드 시작
        if not self.data_thread.is_alive():
            self.data_thread.start()
        
        print(f"🌐 대시보드 서버 시작: http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)
    
    def _collect_data_loop(self):
        """데이터 수집 루프"""
        while self.data_collection_active:
            try:
                # 프로젝트 상태 수집
                self._collect_project_metrics()
                
                # 역할 상태 수집
                self._collect_role_statuses()
                
                # 알림 확인
                self._check_alerts()
                
                # 실시간 데이터 전송
                self._emit_real_time_data()
                
                time.sleep(10)  # 10초마다 수집
                
            except Exception as e:
                print(f"데이터 수집 오류: {str(e)}")
                time.sleep(30)
    
    def _collect_project_metrics(self):
        """프로젝트 메트릭 수집"""
        try:
            # 다른 시스템들에서 메트릭 수집
            # 실제 구현에서는 각 시스템의 API를 호출
            
            # 예시 메트릭 생성
            progress_metric = DashboardMetric(
                metric_id="overall_progress",
                metric_type=DashboardMetricType.PROGRESS,
                name="전체 진행률",
                value=75.5,
                unit="%",
                trend="up",
                target_value=100.0,
                timestamp=datetime.now(),
                role_id=None,
                project_phase="development"
            )
            
            with self.cache_lock:
                self.metrics_cache[progress_metric.metric_id] = progress_metric
            
            # 데이터베이스에 저장
            self._save_metric(progress_metric)
            
        except Exception as e:
            print(f"프로젝트 메트릭 수집 오류: {str(e)}")
    
    def _collect_role_statuses(self):
        """역할 상태 수집"""
        try:
            # 예시 역할 상태들
            example_roles = [
                {
                    "role_id": "business_analyst",
                    "role_name": "Business Analyst",
                    "status": "active",
                    "current_task": "요구사항 분석",
                    "progress_percentage": 65.0,
                    "performance_score": 0.92,
                    "tasks_completed": 8,
                    "tasks_pending": 3,
                    "average_task_time": 2.5
                },
                {
                    "role_id": "frontend_developer",
                    "role_name": "Frontend Developer",
                    "status": "busy",
                    "current_task": "UI 컴포넌트 구현",
                    "progress_percentage": 80.0,
                    "performance_score": 0.88,
                    "tasks_completed": 12,
                    "tasks_pending": 2,
                    "average_task_time": 3.2
                },
                {
                    "role_id": "qa_tester",
                    "role_name": "QA Tester",
                    "status": "idle",
                    "current_task": None,
                    "progress_percentage": 45.0,
                    "performance_score": 0.95,
                    "tasks_completed": 6,
                    "tasks_pending": 5,
                    "average_task_time": 1.8
                }
            ]
            
            with self.cache_lock:
                for role_data in example_roles:
                    role_status = RoleStatus(
                        role_id=role_data["role_id"],
                        role_name=role_data["role_name"],
                        status=role_data["status"],
                        current_task=role_data["current_task"],
                        progress_percentage=role_data["progress_percentage"],
                        last_activity=datetime.now(),
                        performance_score=role_data["performance_score"],
                        tasks_completed=role_data["tasks_completed"],
                        tasks_pending=role_data["tasks_pending"],
                        average_task_time=role_data["average_task_time"]
                    )
                    
                    self.role_status_cache[role_status.role_id] = role_status
                    self._save_role_status(role_status)
            
        except Exception as e:
            print(f"역할 상태 수집 오류: {str(e)}")
    
    def _check_alerts(self):
        """알림 확인"""
        try:
            # 예시 알림 생성 (실제로는 시스템 상태를 확인)
            if len(self.alerts_cache) < 3:  # 테스트용
                alert = DashboardAlert(
                    alert_id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    level=AlertLevel.INFO,
                    title="시스템 정상 작동",
                    message="모든 에이전트가 정상적으로 작동 중입니다.",
                    source="system_monitor",
                    timestamp=datetime.now(),
                    resolved=False,
                    action_required=False,
                    related_metrics=["overall_progress"]
                )
                
                with self.cache_lock:
                    self.alerts_cache[alert.alert_id] = alert
                
                self._save_alert(alert)
            
        except Exception as e:
            print(f"알림 확인 오류: {str(e)}")
    
    def _emit_real_time_data(self):
        """실시간 데이터 전송"""
        try:
            dashboard_data = {
                'overview': self._get_project_overview(),
                'roles': self._get_role_statuses(),
                'alerts': self._get_alerts(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.socketio.emit('dashboard_update', dashboard_data)
            
        except Exception as e:
            print(f"실시간 데이터 전송 오류: {str(e)}")
    
    def _get_project_overview(self) -> Dict[str, Any]:
        """프로젝트 개요 데이터"""
        with self.cache_lock:
            active_roles = len([r for r in self.role_status_cache.values() if r.status == "active"])
            pending_tasks = sum(r.tasks_pending for r in self.role_status_cache.values())
            overall_progress = self.metrics_cache.get("overall_progress")
            
            return {
                'overall_progress': int(overall_progress.value) if overall_progress else 0,
                'active_roles': active_roles,
                'pending_tasks': pending_tasks,
                'alert_count': len(self.alerts_cache)
            }
    
    def _get_metrics(self, metric_type: str = None) -> List[Dict[str, Any]]:
        """메트릭 데이터 조회"""
        with self.cache_lock:
            metrics = list(self.metrics_cache.values())
            
            if metric_type:
                metrics = [m for m in metrics if m.metric_type.value == metric_type]
            
            return [asdict(m) for m in metrics]
    
    def _get_alerts(self, level: str = None) -> List[Dict[str, Any]]:
        """알림 데이터 조회"""
        with self.cache_lock:
            alerts = list(self.alerts_cache.values())
            
            if level:
                alerts = [a for a in alerts if a.level.value == level]
            
            # 최신순 정렬
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            return [asdict(a) for a in alerts[:10]]  # 최근 10개만
    
    def _get_role_statuses(self) -> List[Dict[str, Any]]:
        """역할 상태 데이터 조회"""
        with self.cache_lock:
            return [asdict(r) for r in self.role_status_cache.values()]
    
    def _get_timeline_data(self, days: int = 7) -> List[Dict[str, Any]]:
        """타임라인 데이터 조회"""
        # 예시 타임라인 데이터
        timeline_events = [
            {
                'title': '프로젝트 시작',
                'description': '멀티 에이전트 시스템 초기화 완료',
                'timestamp': (datetime.now() - timedelta(days=5)).isoformat(),
                'role': 'system'
            },
            {
                'title': '요구사항 분석 완료',
                'description': '비즈니스 요구사항 문서 작성 완료',
                'timestamp': (datetime.now() - timedelta(days=3)).isoformat(),
                'role': 'business_analyst'
            },
            {
                'title': 'UI 설계 시작',
                'description': '사용자 인터페이스 설계 작업 시작',
                'timestamp': (datetime.now() - timedelta(days=2)).isoformat(),
                'role': 'ui_ux_designer'
            },
            {
                'title': '백엔드 API 개발',
                'description': 'REST API 엔드포인트 구현 중',
                'timestamp': (datetime.now() - timedelta(days=1)).isoformat(),
                'role': 'backend_developer'
            }
        ]
        
        return timeline_events
    
    def _save_metric(self, metric: DashboardMetric):
        """메트릭 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO dashboard_metrics
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.metric_id, metric.metric_type.value, metric.name,
                str(metric.value), metric.unit, metric.trend,
                str(metric.target_value) if metric.target_value else None,
                metric.timestamp.isoformat(), metric.role_id, metric.project_phase,
                datetime.now().isoformat()
            ))
    
    def _save_alert(self, alert: DashboardAlert):
        """알림 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO dashboard_alerts
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id, alert.level.value, alert.title, alert.message,
                alert.source, alert.timestamp.isoformat(), alert.resolved,
                alert.action_required, json.dumps(alert.related_metrics),
                datetime.now().isoformat()
            ))
    
    def _save_role_status(self, role_status: RoleStatus):
        """역할 상태 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO role_status
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                role_status.role_id, role_status.role_name, role_status.status,
                role_status.current_task, role_status.progress_percentage,
                role_status.last_activity.isoformat(), role_status.performance_score,
                role_status.tasks_completed, role_status.tasks_pending,
                role_status.average_task_time, datetime.now().isoformat()
            ))

def main():
    """테스트 및 데모"""
    dashboard = ProjectDashboardSystem("/home/jungh/workspace/multi_claude_code_sample")
    
    print("📊 프로젝트 대시보드 서버 시작...")
    print("브라우저에서 http://localhost:5000 접속")
    
    # 대시보드 서버 시작
    dashboard.start_dashboard_server(port=5000, debug=True)

if __name__ == "__main__":
    main()