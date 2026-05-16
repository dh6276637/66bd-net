#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 进化核心系统 - 具有参数自学习和防幻觉能力的智能系统
包含：参数化模型、学习进化、防幻觉验证、严格操作定义
"""

import json
import hashlib
import os
import random
import pickle
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from collections import deque, defaultdict


class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_LOW = 0.0
    LOW = 0.25
    MEDIUM = 0.5
    HIGH = 0.75
    VERY_HIGH = 0.95


class OperationType(Enum):
    """操作类型 - 严格定义"""
    READ = "read"           # 只读操作
    WRITE = "write"         # 写入操作
    MODIFY = "modify"       # 修改操作
    DELETE = "delete"       # 删除操作
    UPDATE = "update"       # 更新操作
    EXECUTE = "execute"     # 执行操作
    ANALYZE = "analyze"     # 分析操作
    PREDICT = "predict"     # 预测操作


class SafetyLevel(Enum):
    """安全等级"""
    SAFE = 0              # 完全安全
    LOW_RISK = 1          # 低风险
    MEDIUM_RISK = 2       # 中等风险
    HIGH_RISK = 3         # 高风险
    DANGEROUS = 4         # 危险操作，需要严格验证


@dataclass
class Parameter:
    """AI参数模型"""
    name: str
    value: Any
    type: str = "float"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    adaptive: bool = True  # 是否可自适应调整
    learning_rate: float = 0.01  # 学习速率
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.5  # 参数置信度
    history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
    
    def update(self, new_value: Any, feedback: float = 0.0, source: str = "manual") -> bool:
        """更新参数值并记录历史"""
        old_value = self.value
        
        # 记录历史
        self.history.append({
            'old_value': old_value,
            'new_value': new_value,
            'feedback': feedback,
            'source': source,
            'timestamp': datetime.now().isoformat()
        })
        
        # 保留最近100条历史
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        self.value = new_value
        self.last_updated = datetime.now().isoformat()
        
        # 根据反馈调整置信度
        if feedback > 0:
            self.confidence = min(1.0, self.confidence + feedback * 0.1)
        elif feedback < 0:
            self.confidence = max(0.0, self.confidence + feedback * 0.2)
        
        return True
    
    def learn_from_feedback(self, feedback: float) -> None:
        """根据反馈学习调整"""
        if not self.adaptive:
            return
        
        if self.type == "float" and isinstance(self.value, (int, float)):
            adjustment = feedback * self.learning_rate
            new_value = self.value + adjustment
            
            if self.min_value is not None:
                new_value = max(self.min_value, new_value)
            if self.max_value is not None:
                new_value = min(self.max_value, new_value)
            
            self.update(new_value, feedback, "feedback_learning")
    
    def get_weighted_value(self) -> Any:
        """获取加权值（考虑置信度）"""
        if self.type == "float" and isinstance(self.value, (int, float)):
            return self.value * self.confidence
        return self.value


@dataclass
class StrictOperation:
    """严格定义的操作"""
    name: str
    operation_type: OperationType
    safety_level: SafetyLevel
    description: str
    required_params: List[str]
    validation_rules: Dict[str, Any]
    handler: Optional[Callable] = None
    max_executions_per_minute: int = 60
    enabled: bool = True
    requires_approval: bool = False
    
    def validate(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """严格验证操作参数"""
        for required in self.required_params:
            if required not in params or params[required] is None:
                return False, f"缺少必需参数: {required}"
        
        for param_name, rules in self.validation_rules.items():
            if param_name in params:
                value = params[param_name]
                
                if 'type' in rules:
                    expected_type = rules['type']
                    if not isinstance(value, expected_type):
                        return False, f"参数 {param_name} 类型错误，期望 {expected_type}"
                
                if 'min' in rules and value < rules['min']:
                    return False, f"参数 {param_name} 小于最小值 {rules['min']}"
                
                if 'max' in rules and value > rules['max']:
                    return False, f"参数 {param_name} 大于最大值 {rules['max']}"
                
                if 'allowed_values' in rules and value not in rules['allowed_values']:
                    return False, f"参数 {param_name} 不在允许值列表中"
        
        return True, "验证通过"


@dataclass
class Experience:
    """AI经验记录"""
    id: str
    timestamp: str
    situation: Dict[str, Any]
    action: str
    parameters: Dict[str, Any]
    outcome: Any
    reward: float
    success: bool
    feedback_score: float
    context_hash: str


class HallucinationGuard:
    """防幻觉系统"""
    
    def __init__(self):
        self.fact_database: Dict[str, Dict] = {}
        self.claim_history: List[Dict] = []
        self.validation_rules: List[Callable] = []
        self.confidence_threshold = 0.3
        
        self._init_validation_rules()
        self._load_facts()
    
    def _init_validation_rules(self):
        """初始化验证规则"""
        self.validation_rules = [
            self._check_fact_consistency,
            self._check_source_reliability,
            self._check_logical_coherence,
            self._check_plausibility
        ]
    
    def _load_facts(self):
        """加载事实库"""
        self.fact_database = {
            "site_structure": {
                "has_admin": True,
                "has_public": True,
                "database_exists": True,
                "confidence": 1.0
            },
            "safe_operations": [
                "analyze", "read", "predict", "search"
            ],
            "risky_operations": [
                "delete", "modify", "update", "execute"
            ]
        }
    
    def _check_fact_consistency(self, claim: Dict) -> Tuple[bool, float, str]:
        """检查与事实库一致性"""
        claim_type = claim.get('type', '')
        
        if claim_type == 'site_fact':
            claimed_fact = claim.get('fact', '')
            if claimed_fact in self.fact_database:
                fact = self.fact_database[claimed_fact]
                if fact.get('confidence', 0) > 0.8:
                    return True, fact['confidence'], "与事实库一致"
        
        return True, 0.5, "事实库中无此信息"
    
    def _check_source_reliability(self, claim: Dict) -> Tuple[bool, float, str]:
        """检查信息来源可靠性"""
        source = claim.get('source', 'unknown')
        
        reliable_sources = ['database', 'system_log', 'user_feedback', 'github']
        if source in reliable_sources:
            return True, 0.9, "来源可靠"
        
        if source == 'ai_inference':
            return True, 0.6, "AI推断，中等可信度"
        
        return False, 0.2, "来源不明"
    
    def _check_logical_coherence(self, claim: Dict) -> Tuple[bool, float, str]:
        """检查逻辑一致性"""
        content = str(claim.get('content', ''))
        
        if 'impossible' in content.lower() or 'cannot' in content.lower():
            if 'possible' in content.lower() or 'can' in content.lower():
                return False, 0.1, "逻辑矛盾"
        
        return True, 0.8, "逻辑一致"
    
    def _check_plausibility(self, claim: Dict) -> Tuple[bool, float, str]:
        """检查合理性"""
        confidence = claim.get('confidence', 0)
        
        if confidence > 0.95:
            return True, 0.9, "高置信度声明"
        
        if confidence < self.confidence_threshold:
            return False, confidence, "置信度低于阈值"
        
        return True, confidence, "置信度适中"
    
    def validate_claim(self, claim: Dict) -> Tuple[bool, float, List[str]]:
        """验证声明是否存在幻觉"""
        results = []
        overall_confidence = 1.0
        warnings = []
        
        for rule in self.validation_rules:
            try:
                valid, confidence, reason = rule(claim)
                if not valid:
                    warnings.append(reason)
                results.append((valid, confidence, reason))
                overall_confidence *= confidence
            except Exception as e:
                warnings.append(f"验证规则执行错误: {e}")
        
        self.claim_history.append({
            'claim': claim,
            'results': results,
            'overall_confidence': overall_confidence,
            'timestamp': datetime.now().isoformat()
        })
        
        return overall_confidence >= self.confidence_threshold, overall_confidence, warnings
    
    def add_fact(self, fact_id: str, fact_data: Dict, confidence: float = 0.8) -> None:
        """添加事实到事实库"""
        fact_data['confidence'] = confidence
        fact_data['added_at'] = datetime.now().isoformat()
        self.fact_database[fact_id] = fact_data
    
    def get_confidence_level(self, claim: Dict) -> ConfidenceLevel:
        """获取置信度等级"""
        is_valid, confidence, _ = self.validate_claim(claim)
        
        if not is_valid:
            return ConfidenceLevel.VERY_LOW
        elif confidence < 0.25:
            return ConfidenceLevel.LOW
        elif confidence < 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence < 0.9:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH


class ParameterModel:
    """参数化AI模型"""
    
    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.parameters: Dict[str, Parameter] = {}
        self.version: int = 1
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = datetime.now().isoformat()
        self.performance_history: List[Dict] = []
        
        self._init_default_parameters()
    
    def _init_default_parameters(self):
        """初始化默认参数"""
        self.parameters = {
            "learning_rate": Parameter(
                name="learning_rate",
                value=0.01,
                type="float",
                min_value=0.0001,
                max_value=0.1,
                description="学习速率",
                adaptive=True,
                confidence=0.8
            ),
            "exploration_rate": Parameter(
                name="exploration_rate",
                value=0.2,
                type="float",
                min_value=0.0,
                max_value=1.0,
                description="探索率（尝试新策略的概率）",
                adaptive=True,
                confidence=0.6
            ),
            "confidence_threshold": Parameter(
                name="confidence_threshold",
                value=0.7,
                type="float",
                min_value=0.3,
                max_value=0.95,
                description="决策置信度阈值",
                adaptive=True,
                confidence=0.9
            ),
            "safety_factor": Parameter(
                name="safety_factor",
                value=2.0,
                type="float",
                min_value=1.0,
                max_value=5.0,
                description="安全系数（保守程度）",
                adaptive=True,
                confidence=0.85
            ),
            "optimization_aggressiveness": Parameter(
                name="optimization_aggressiveness",
                value=0.5,
                type="float",
                min_value=0.1,
                max_value=1.0,
                description="优化激进程度",
                adaptive=True,
                confidence=0.7
            ),
            "pattern_sensitivity": Parameter(
                name="pattern_sensitivity",
                value=0.6,
                type="float",
                min_value=0.1,
                max_value=1.0,
                description="模式识别敏感度",
                adaptive=True,
                confidence=0.75
            ),
            "feedback_weight": Parameter(
                name="feedback_weight",
                value=0.8,
                type="float",
                min_value=0.0,
                max_value=1.0,
                description="用户反馈权重",
                adaptive=True,
                confidence=0.9
            ),
            "memory_decay_rate": Parameter(
                name="memory_decay_rate",
                value=0.05,
                type="float",
                min_value=0.001,
                max_value=0.2,
                description="记忆衰减率",
                adaptive=True,
                confidence=0.65
            )
        }
    
    def get_param(self, name: str) -> Optional[Parameter]:
        """获取参数"""
        return self.parameters.get(name)
    
    def get_param_value(self, name: str, default: Any = None) -> Any:
        """获取参数值"""
        param = self.get_param(name)
        if param:
            return param.get_weighted_value()
        return default
    
    def update_parameter(self, name: str, value: Any, feedback: float = 0.0) -> bool:
        """更新参数"""
        param = self.get_param(name)
        if param:
            success = param.update(value, feedback, "model_update")
            if success:
                self.updated_at = datetime.now().isoformat()
                self.version += 1
            return success
        return False
    
    def apply_feedback(self, feedback: float) -> None:
        """应用反馈到所有可自适应参数"""
        for param in self.parameters.values():
            if param.adaptive:
                param.learn_from_feedback(feedback)
        
        self.record_performance(feedback)
        self.version += 1
        self.updated_at = datetime.now().isoformat()
    
    def record_performance(self, score: float) -> None:
        """记录性能"""
        self.performance_history.append({
            'score': score,
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                k: v.value for k, v in self.parameters.items()
            }
        })
        
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def evolve_parameters(self) -> Dict[str, Any]:
        """进化参数 - 基于历史表现"""
        if len(self.performance_history) < 10:
            return {"status": "insufficient_data"}
        
        recent = self.performance_history[-50:]
        
        good_performances = [p for p in recent if p['score'] > 0.7]
        bad_performances = [p for p in recent if p['score'] < 0.3]
        
        changes = {}
        
        for param_name in self.parameters:
            param = self.parameters[param_name]
            if not param.adaptive:
                continue
            
            if good_performances:
                good_values = [p['parameters'].get(param_name) for p in good_performances if p['parameters'].get(param_name) is not None]
                if good_values:
                    avg_good = sum(good_values) / len(good_values)
                    current = param.value
                    adjustment = (avg_good - current) * 0.1
                    
                    new_value = current + adjustment
                    if param.min_value is not None:
                        new_value = max(param.min_value, new_value)
                    if param.max_value is not None:
                        new_value = min(param.max_value, new_value)
                    
                    param.update(new_value, 0.3, "evolution")
                    changes[param_name] = {'old': current, 'new': new_value}
        
        return {
            "status": "evolved",
            "changes": changes,
            "version": self.version
        }
    
    def save(self, filepath: str) -> bool:
        """保存模型"""
        try:
            data = {
                'model_name': self.model_name,
                'version': self.version,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'parameters': {
                    k: {
                        'name': v.name,
                        'value': v.value,
                        'type': v.type,
                        'min_value': v.min_value,
                        'max_value': v.max_value,
                        'description': v.description,
                        'adaptive': v.adaptive,
                        'learning_rate': v.learning_rate,
                        'last_updated': v.last_updated,
                        'confidence': v.confidence,
                        'history': v.history
                    } for k, v in self.parameters.items()
                },
                'performance_history': self.performance_history
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存模型失败: {e}")
            return False
    
    @classmethod
    def load(cls, filepath: str) -> Optional['ParameterModel']:
        """加载模型"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            model = cls(data.get('model_name', 'loaded_model'))
            model.version = data.get('version', 1)
            model.created_at = data.get('created_at', model.created_at)
            model.updated_at = data.get('updated_at', model.updated_at)
            model.performance_history = data.get('performance_history', [])
            
            for name, param_data in data.get('parameters', {}).items():
                param = Parameter(
                    name=param_data['name'],
                    value=param_data['value'],
                    type=param_data.get('type', 'float'),
                    min_value=param_data.get('min_value'),
                    max_value=param_data.get('max_value'),
                    description=param_data.get('description', ''),
                    adaptive=param_data.get('adaptive', True),
                    learning_rate=param_data.get('learning_rate', 0.01),
                    last_updated=param_data.get('last_updated'),
                    confidence=param_data.get('confidence', 0.5),
                    history=param_data.get('history', [])
                )
                model.parameters[name] = param
            
            return model
        except Exception as e:
            print(f"加载模型失败: {e}")
            return None


class LearningEngine:
    """学习引擎"""
    
    def __init__(self, model: ParameterModel):
        self.model = model
        self.experiences: deque = deque(maxlen=10000)
        self.patterns: Dict[str, List[Dict]] = defaultdict(list)
        self.success_stats: Dict[str, Dict] = defaultdict(lambda: {'success': 0, 'total': 0})
        self.lock = threading.Lock()
    
    def add_experience(self, situation: Dict, action: str, params: Dict, 
                      outcome: Any, reward: float, success: bool) -> str:
        """添加经验"""
        exp_id = hashlib.md5(
            f"{datetime.now().isoformat()}-{action}".encode()
        ).hexdigest()[:12]
        
        context_hash = hashlib.md5(
            json.dumps(situation, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        experience = Experience(
            id=exp_id,
            timestamp=datetime.now().isoformat(),
            situation=situation,
            action=action,
            parameters=params,
            outcome=outcome,
            reward=reward,
            success=success,
            feedback_score=reward,
            context_hash=context_hash
        )
        
        with self.lock:
            self.experiences.append(experience)
            self.patterns[context_hash].append({
                'action': action,
                'reward': reward,
                'success': success,
                'timestamp': experience.timestamp
            })
            
            self.success_stats[action]['total'] += 1
            if success:
                self.success_stats[action]['success'] += 1
        
        return exp_id
    
    def learn_from_experience(self, experience: Experience) -> float:
        """从经验中学习"""
        feedback = experience.reward
        
        if experience.success:
            feedback = min(1.0, feedback + 0.2)
        else:
            feedback = max(-1.0, feedback - 0.2)
        
        self.model.apply_feedback(feedback)
        
        return feedback
    
    def get_success_rate(self, action: str) -> float:
        """获取操作成功率"""
        stats = self.success_stats.get(action, {'success': 0, 'total': 0})
        if stats['total'] == 0:
            return 0.5
        return stats['success'] / stats['total']
    
    def get_best_action(self, situation: Dict) -> Optional[str]:
        """获取最佳行动"""
        context_hash = hashlib.md5(
            json.dumps(situation, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        if context_hash not in self.patterns:
            return None
        
        pattern = self.patterns[context_hash]
        
        action_rewards: Dict[str, List[float]] = defaultdict(list)
        for item in pattern:
            action_rewards[item['action']].append(item['reward'])
        
        if not action_rewards:
            return None
        
        avg_rewards = {
            action: sum(rewards) / len(rewards)
            for action, rewards in action_rewards.items()
        }
        
        return max(avg_rewards.items(), key=lambda x: x[1])[0]
    
    def get_recommendation(self, situation: Dict) -> Dict[str, Any]:
        """获取推荐"""
        context_hash = hashlib.md5(
            json.dumps(situation, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        if context_hash in self.patterns:
            pattern = self.patterns[context_hash]
            
            if pattern:
                recent = pattern[-20:]
                success_rate = sum(1 for x in recent if x['success']) / len(recent)
                avg_reward = sum(x['reward'] for x in recent) / len(recent)
                
                return {
                    'from_memory': True,
                    'context_hash': context_hash,
                    'similar_cases': len(pattern),
                    'success_rate': success_rate,
                    'avg_reward': avg_reward,
                    'recommended_action': self.get_best_action(situation)
                }
        
        return {
            'from_memory': False,
            'reason': 'no_similar_situation'
        }


class SelfImprovementEngine:
    """自我改进引擎"""
    
    def __init__(self, model: ParameterModel, learning_engine: LearningEngine):
        self.model = model
        self.learning_engine = learning_engine
        self.improvement_history: List[Dict] = []
        self.auto_evolve_enabled: bool = True
        self.last_evolution: Optional[str] = None
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析性能"""
        if len(self.model.performance_history) < 10:
            return {
                'status': 'insufficient_data',
                'recommendations': ['collect_more_data']
            }
        
        recent = self.model.performance_history[-50:]
        older = self.model.performance_history[-100:-50] if len(self.model.performance_history) > 100 else []
        
        recent_avg = sum(p['score'] for p in recent) / len(recent)
        
        if older:
            older_avg = sum(p['score'] for p in older) / len(older)
            trend = 'improving' if recent_avg > older_avg + 0.05 else \
                    'declining' if recent_avg < older_avg - 0.05 else 'stable'
        else:
            trend = 'unknown'
        
        recommendations = []
        if recent_avg < 0.5:
            recommendations.append('increase_exploration')
            recommendations.append('review_parameters')
        elif recent_avg > 0.8:
            recommendations.append('decrease_exploration')
            recommendations.append('solidify_winning_strategies')
        
        return {
            'status': 'analyzed',
            'recent_performance': recent_avg,
            'trend': trend,
            'recommendations': recommendations
        }
    
    def evolve(self) -> Dict[str, Any]:
        """执行进化"""
        if not self.auto_evolve_enabled:
            return {'status': 'evolution_disabled'}
        
        result = self.model.evolve_parameters()
        
        if result.get('status') == 'evolved':
            self.last_evolution = datetime.now().isoformat()
            self.improvement_history.append({
                'type': 'evolution',
                'timestamp': self.last_evolution,
                'result': result
            })
        
        return result
    
    def self_improve(self) -> Dict[str, Any]:
        """执行自我改进循环"""
        analysis = self.analyze_performance()
        
        if analysis.get('status') == 'insufficient_data':
            return analysis
        
        evolution_result = self.evolve()
        
        self.improvement_history.append({
            'type': 'self_improvement',
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'evolution': evolution_result
        })
        
        return {
            'status': 'completed',
            'analysis': analysis,
            'evolution': evolution_result,
            'history_count': len(self.improvement_history)
        }


class StrictOperationExecutor:
    """严格操作执行器"""
    
    def __init__(self, hallucination_guard: HallucinationGuard):
        self.hallucination_guard = hallucination_guard
        self.operations: Dict[str, StrictOperation] = {}
        self.execution_history: deque = deque(maxlen=1000)
        self.rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
        self.lock = threading.Lock()
    
    def register_operation(self, operation: StrictOperation) -> None:
        """注册操作"""
        self.operations[operation.name] = operation
    
    def check_rate_limit(self, operation_name: str) -> Tuple[bool, str]:
        """检查速率限制"""
        operation = self.operations.get(operation_name)
        if not operation:
            return False, "操作未注册"
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        recent_executions = [
            t for t in self.rate_limits[operation_name]
            if t > minute_ago
        ]
        
        self.rate_limits[operation_name] = deque(recent_executions, maxlen=60)
        
        if len(recent_executions) >= operation.max_executions_per_minute:
            return False, f"超过速率限制: {operation.max_executions_per_minute}/分钟"
        
        return True, "OK"
    
    def execute_operation(self, operation_name: str, params: Dict, 
                        source: str = "ai") -> Dict[str, Any]:
        """执行严格操作"""
        operation = self.operations.get(operation_name)
        if not operation:
            return {
                'success': False,
                'error': f"未知操作: {operation_name}",
                'code': 'unknown_operation'
            }
        
        if not operation.enabled:
            return {
                'success': False,
                'error': f"操作已禁用: {operation_name}",
                'code': 'operation_disabled'
            }
        
        rate_ok, rate_msg = self.check_rate_limit(operation_name)
        if not rate_ok:
            return {
                'success': False,
                'error': rate_msg,
                'code': 'rate_limit_exceeded'
            }
        
        is_valid, validation_msg = operation.validate(params)
        if not is_valid:
            return {
                'success': False,
                'error': f"参数验证失败: {validation_msg}",
                'code': 'validation_failed'
            }
        
        claim = {
            'type': 'operation',
            'operation': operation_name,
            'params': params,
            'source': source,
            'confidence': 0.8
        }
        
        hallucination_ok, hallucination_confidence, warnings = \
            self.hallucination_guard.validate_claim(claim)
        
        if not hallucination_ok:
            return {
                'success': False,
                'error': f"防幻觉验证失败: {warnings}",
                'code': 'hallucination_detected',
                'warnings': warnings
            }
        
        if operation.requires_approval and operation.safety_level.value >= SafetyLevel.HIGH_RISK.value:
            return {
                'success': False,
                'error': "高风险操作需要人工审批",
                'code': 'approval_required'
            }
        
        with self.lock:
            self.rate_limits[operation_name].append(datetime.now())
        
        result = {
            'success': True,
            'operation': operation_name,
            'safety_level': operation.safety_level.name,
            'confidence': hallucination_confidence,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
        
        if operation.handler:
            try:
                handler_result = operation.handler(params)
                result['handler_result'] = handler_result
            except Exception as e:
                result['success'] = False
                result['error'] = f"操作执行失败: {e}"
                result['code'] = 'execution_failed'
        
        self.execution_history.append({
            'operation': operation_name,
            'params': params,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result


class AIEvolutionCore:
    """AI 进化核心"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/tmp/ai_evolution_model.json"
        
        self.model = self._load_or_create_model()
        self.hallucination_guard = HallucinationGuard()
        self.learning_engine = LearningEngine(self.model)
        self.self_improvement = SelfImprovementEngine(self.model, self.learning_engine)
        self.operation_executor = StrictOperationExecutor(self.hallucination_guard)
        
        self.start_time = datetime.now()
        self.is_running = False
        
        self._register_default_operations()
    
    def _load_or_create_model(self) -> ParameterModel:
        """加载或创建模型"""
        if os.path.exists(self.model_path):
            model = ParameterModel.load(self.model_path)
            if model:
                print(f"已加载AI模型: {model.model_name} v{model.version}")
                return model
        
        print("创建新的AI模型")
        return ParameterModel("site_ai_core")
    
    def _register_default_operations(self):
        """注册默认操作"""
        self.operation_executor.register_operation(StrictOperation(
            name="analyze_content",
            operation_type=OperationType.ANALYZE,
            safety_level=SafetyLevel.SAFE,
            description="分析内容质量",
            required_params=["content_id"],
            validation_rules={
                "content_id": {"type": int, "min": 1}
            }
        ))
        
        self.operation_executor.register_operation(StrictOperation(
            name="classify_article",
            operation_type=OperationType.ANALYZE,
            safety_level=SafetyLevel.LOW_RISK,
            description="智能分类文章",
            required_params=["article_id"],
            validation_rules={
                "article_id": {"type": int, "min": 1}
            }
        ))
        
        self.operation_executor.register_operation(StrictOperation(
            name="update_setting",
            operation_type=OperationType.MODIFY,
            safety_level=SafetyLevel.MEDIUM_RISK,
            description="更新系统设置",
            required_params=["setting_key", "setting_value"],
            validation_rules={
                "setting_key": {"type": str},
                "setting_value": {"type": str}
            },
            requires_approval=True
        ))
        
        self.operation_executor.register_operation(StrictOperation(
            name="optimize_layout",
            operation_type=OperationType.UPDATE,
            safety_level=SafetyLevel.LOW_RISK,
            description="优化布局建议",
            required_params=["page"],
            validation_rules={
                "page": {"type": str}
            }
        ))
        
        self.operation_executor.register_operation(StrictOperation(
            name="generate_summary",
            operation_type=OperationType.ANALYZE,
            safety_level=SafetyLevel.SAFE,
            description="生成内容摘要",
            required_params=["content"],
            validation_rules={
                "content": {"type": str}
            }
        ))
    
    def process(self, request: Dict) -> Dict[str, Any]:
        """处理请求"""
        request_id = hashlib.md5(
            f"{datetime.now().isoformat()}-{json.dumps(request)}".encode()
        ).hexdigest()[:12]
        
        result = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'model_version': self.model.version
        }
        
        request_type = request.get('type', 'unknown')
        
        if request_type == 'operation':
            op_result = self.operation_executor.execute_operation(
                request.get('operation'),
                request.get('params', {}),
                request.get('source', 'user')
            )
            result['operation_result'] = op_result
            
            if op_result.get('success'):
                feedback = 0.5
            else:
                feedback = -0.3
            self.learning_engine.add_experience(
                request, request.get('operation'),
                request.get('params', {}),
                op_result, feedback,
                op_result.get('success', False)
            )
        
        elif request_type == 'query':
            recommendation = self.learning_engine.get_recommendation(request)
            result['recommendation'] = recommendation
        
        elif request_type == 'get_suggestions':
            analysis = self.self_improvement.analyze_performance()
            result['suggestions'] = analysis
        
        elif request_type == 'evolve':
            evolution_result = self.self_improvement.self_improve()
            result['evolution'] = evolution_result
            self.model.save(self.model_path)
        
        elif request_type == 'add_feedback':
            feedback = request.get('feedback', 0)
            self.model.apply_feedback(feedback)
            self.model.save(self.model_path)
            result['feedback_applied'] = feedback
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'uptime': str(datetime.now() - self.start_time),
            'model_version': self.model.version,
            'model_name': self.model.model_name,
            'parameters_count': len(self.model.parameters),
            'experiences_count': len(self.learning_engine.experiences),
            'improvement_history_count': len(self.self_improvement.improvement_history),
            'operations_count': len(self.operation_executor.execution_history),
            'is_running': self.is_running
        }
    
    def save(self) -> bool:
        """保存模型"""
        return self.model.save(self.model_path)


_global_ai_core: Optional[AIEvolutionCore] = None


def get_ai_core(model_path: Optional[str] = None) -> AIEvolutionCore:
    """获取AI核心单例"""
    global _global_ai_core
    if _global_ai_core is None:
        _global_ai_core = AIEvolutionCore(model_path)
    return _global_ai_core


if __name__ == "__main__":
    print("🚀 AI Evolution Core - Self-Learning AI System")
    print("=" * 60)
    
    ai_core = get_ai_core()
    
    print(f"\n✅ AI Core initialized:")
    print(f"   Model: {ai_core.model.model_name} v{ai_core.model.version}")
    print(f"   Parameters: {len(ai_core.model.parameters)}")
    print(f"\n🧪 Running self-test...")
    
    test_request = {
        'type': 'operation',
        'operation': 'analyze_content',
        'params': {'content_id': 123},
        'source': 'system'
    }
    
    result = ai_core.process(test_request)
    print(f"\n📊 Test result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    print(f"\n✅ AI System ready!")
