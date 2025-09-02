"""
Core behavior tree nodes - extracted from ai_behaviors.py
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Status wykonania węzła"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode(ABC):
    """Abstrakcyjna klasa bazowa dla węzłów behavior tree"""
    
    def __init__(self, name: str):
        self.name = name
        self.children: List['BehaviorNode'] = []
        self.parent: Optional['BehaviorNode'] = None
    
    def add_child(self, child: 'BehaviorNode'):
        """Dodaje dziecko do węzła"""
        child.parent = self
        self.children.append(child)
    
    @abstractmethod
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        """Wykonuje węzeł"""
        pass
    
    def reset(self):
        """Resetuje stan węzła"""
        for child in self.children:
            child.reset()


class CompositeNode(BehaviorNode):
    """Węzeł kompozytowy z dziećmi"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.current_child = 0


class SelectorNode(CompositeNode):
    """Węzeł selektor - wykonuje dzieci do pierwszego sukcesu"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        for child in self.children:
            result = child.execute(npc, context)
            if result == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif result == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE


class SequenceNode(CompositeNode):
    """Węzeł sekwencja - wykonuje wszystkie dzieci po kolei"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        for child in self.children:
            result = child.execute(npc, context)
            if result == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            elif result == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.SUCCESS


class RandomSelectorNode(CompositeNode):
    """Losowy selektor"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        import random
        if not self.children:
            return NodeStatus.FAILURE
        
        # Przetasuj dzieci
        children = list(self.children)
        random.shuffle(children)
        
        for child in children:
            result = child.execute(npc, context)
            if result == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif result == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        
        return NodeStatus.FAILURE


class PriorityNode(CompositeNode):
    """Węzeł z priorytetami"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.child_priorities: Dict[BehaviorNode, float] = {}
    
    def add_child_with_priority(self, child: BehaviorNode, priority: float):
        """Dodaje dziecko z priorytetem"""
        self.add_child(child)
        self.child_priorities[child] = priority
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        # Sortuj dzieci wg priorytetu
        sorted_children = sorted(self.children, 
                               key=lambda c: self.child_priorities.get(c, 0), 
                               reverse=True)
        
        for child in sorted_children:
            result = child.execute(npc, context)
            if result == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            elif result == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        
        return NodeStatus.FAILURE


class DecoratorNode(BehaviorNode):
    """Węzeł dekorator - modyfikuje zachowanie dziecka"""
    
    def __init__(self, name: str, child: Optional[BehaviorNode] = None):
        super().__init__(name)
        if child:
            self.add_child(child)
    
    @property
    def child(self) -> Optional[BehaviorNode]:
        return self.children[0] if self.children else None


class InverterNode(DecoratorNode):
    """Odwraca wynik dziecka"""
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        if not self.child:
            return NodeStatus.FAILURE
        
        result = self.child.execute(npc, context)
        if result == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        elif result == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        else:
            return result


class RepeatNode(DecoratorNode):
    """Powtarza dziecko określoną liczbę razy"""
    
    def __init__(self, name: str, repeat_count: int = 1, child: Optional[BehaviorNode] = None):
        super().__init__(name, child)
        self.repeat_count = repeat_count
        self.current_count = 0
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        if not self.child:
            return NodeStatus.FAILURE
        
        while self.current_count < self.repeat_count:
            result = self.child.execute(npc, context)
            
            if result == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            elif result == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            
            self.current_count += 1
        
        self.current_count = 0  # Reset dla następnego wywołania
        return NodeStatus.SUCCESS
    
    def reset(self):
        super().reset()
        self.current_count = 0


class ConditionNode(BehaviorNode):
    """Węzeł warunek"""
    
    def __init__(self, name: str, condition_func):
        super().__init__(name)
        self.condition_func = condition_func
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        try:
            if self.condition_func(npc, context):
                return NodeStatus.SUCCESS
            else:
                return NodeStatus.FAILURE
        except Exception as e:
            logger.error(f"Błąd w warunku {self.name}: {e}")
            return NodeStatus.FAILURE


class ActionNode(BehaviorNode):
    """Węzeł akcja"""
    
    def __init__(self, name: str, action_func):
        super().__init__(name)
        self.action_func = action_func
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        try:
            result = self.action_func(npc, context)
            return result if isinstance(result, NodeStatus) else NodeStatus.SUCCESS
        except Exception as e:
            logger.error(f"Błąd w akcji {self.name}: {e}")
            return NodeStatus.FAILURE


class BlackboardNode(BehaviorNode):
    """Węzeł z dostępem do tablicy"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.blackboard: Dict[str, Any] = {}
    
    def set_value(self, key: str, value: Any):
        """Ustawia wartość na tablicy"""
        self.blackboard[key] = value
    
    def get_value(self, key: str, default=None):
        """Pobiera wartość z tablicy"""
        return self.blackboard.get(key, default)
    
    def execute(self, npc: Any, context: Dict) -> NodeStatus:
        # Udostępnij blackboard w kontekście
        context["blackboard"] = self.blackboard
        
        # Wykonaj wszystkie dzieci
        for child in self.children:
            result = child.execute(npc, context)
            if result != NodeStatus.SUCCESS:
                return result
        
        return NodeStatus.SUCCESS