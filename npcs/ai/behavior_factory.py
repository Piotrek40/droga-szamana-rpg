"""
Behavior tree factory for creating NPC AI behaviors
"""

from typing import Dict, Any
from .behavior_nodes import (
    SelectorNode, SequenceNode, RandomSelectorNode, PriorityNode,
    ConditionNode, ActionNode, BlackboardNode
)
from .conditions import *
from .basic_actions import *


def create_basic_npc_behavior(npc_type: str = "prisoner") -> BlackboardNode:
    """Creates a basic behavior tree for NPCs"""
    
    # Root node with blackboard
    root = BlackboardNode("npc_behavior_root")
    
    # Priority-based selector
    priority_root = PriorityNode("priority_behaviors")
    
    # Emergency behaviors (highest priority)
    emergency = SelectorNode("emergency_responses")
    emergency.add_child(SequenceNode("medical_emergency").add_child(
        ConditionNode("is_medical_emergency", is_medical_emergency)
    ))
    emergency.add_child(SequenceNode("danger_response").add_child(
        ConditionNode("is_in_danger", is_in_danger)
    ))
    priority_root.add_child_with_priority(emergency, 100.0)
    
    # Basic needs (high priority)
    needs = SelectorNode("basic_needs")
    
    # Rest when tired
    rest_sequence = SequenceNode("rest_when_tired")
    rest_sequence.add_child(ConditionNode("is_tired", is_tired))
    rest_sequence.add_child(ActionNode("rest", rest))
    needs.add_child(rest_sequence)
    
    # Meal time
    meal_sequence = SequenceNode("meal_time")
    meal_sequence.add_child(ConditionNode("is_meal_time", is_meal_time))
    meal_sequence.add_child(ConditionNode("is_hungry", is_hungry))
    needs.add_child(meal_sequence)
    
    priority_root.add_child_with_priority(needs, 80.0)
    
    # Goals and tasks (medium priority)
    goals = SelectorNode("goal_pursuit")
    
    urgent_goals = SequenceNode("urgent_goals")
    urgent_goals.add_child(ConditionNode("has_urgent_goal", has_urgent_goal))
    urgent_goals.add_child(ActionNode("work_on_goal", work_on_goal))
    goals.add_child(urgent_goals)
    
    priority_root.add_child_with_priority(goals, 50.0)
    
    # Social interactions (medium-low priority)
    social = SelectorNode("social_behaviors")
    
    social_hour = SequenceNode("social_time")
    social_hour.add_child(ConditionNode("is_social_hour", is_social_hour))
    social_hour.add_child(ActionNode("personal_activity", personal_activity))
    social.add_child(social_hour)
    
    priority_root.add_child_with_priority(social, 30.0)
    
    # Default behaviors (lowest priority)
    default_behavior = RandomSelectorNode("default_behavior")
    default_behavior.add_child(ActionNode("rest", rest))
    default_behavior.add_child(ActionNode("explore", explore_area))
    default_behavior.add_child(ActionNode("observe_surroundings", observe_environment))
    default_behavior.add_child(ActionNode("maintain_equipment", maintain_items))
    default_behavior.add_child(ActionNode("personal_time", personal_activity))
    
    priority_root.add_child_with_priority(default_behavior, 10.0)
    
    # Add priority system to root
    root.add_child(priority_root)
    
    return root


def create_guard_behavior() -> BlackboardNode:
    """Creates behavior tree for guard NPCs"""
    
    root = BlackboardNode("guard_behavior_root")
    priority_root = PriorityNode("guard_priorities")
    
    # Guard duties (highest priority)
    guard_duties = SelectorNode("guard_duties")
    
    patrol_sequence = SequenceNode("patrol_duty")
    patrol_sequence.add_child(ConditionNode("is_guard_patrol_time", is_guard_patrol_time))
    patrol_sequence.add_child(ActionNode("explore", explore_area))  # Patrol is exploration
    guard_duties.add_child(patrol_sequence)
    
    watch_sequence = SequenceNode("watch_prisoners")
    watch_sequence.add_child(ConditionNode("is_day_time", is_day_time))
    watch_sequence.add_child(ActionNode("observe_surroundings", observe_environment))
    guard_duties.add_child(watch_sequence)
    
    priority_root.add_child_with_priority(guard_duties, 90.0)
    
    # Basic needs
    needs = SelectorNode("guard_needs")
    rest_sequence = SequenceNode("rest_when_tired")
    rest_sequence.add_child(ConditionNode("is_tired", is_tired))
    rest_sequence.add_child(ActionNode("rest", rest))
    needs.add_child(rest_sequence)
    
    priority_root.add_child_with_priority(needs, 70.0)
    
    # Default guard behavior
    default_guard = RandomSelectorNode("default_guard_behavior")
    default_guard.add_child(ActionNode("observe_surroundings", observe_environment))
    default_guard.add_child(ActionNode("maintain_equipment", maintain_items))
    default_guard.add_child(ActionNode("rest", rest))
    
    priority_root.add_child_with_priority(default_guard, 20.0)
    
    root.add_child(priority_root)
    return root


def create_prisoner_behavior() -> BlackboardNode:
    """Creates behavior tree for prisoner NPCs"""
    
    root = BlackboardNode("prisoner_behavior_root")
    priority_root = PriorityNode("prisoner_priorities")
    
    # Survival (highest priority)
    survival = SelectorNode("survival_behaviors")
    
    hide_contraband = SequenceNode("hide_contraband")
    hide_contraband.add_child(ConditionNode("has_contraband", has_contraband))
    hide_contraband.add_child(ConditionNode("is_being_watched", is_being_watched))
    survival.add_child(hide_contraband)
    
    escape_planning = SequenceNode("escape_planning")
    escape_planning.add_child(ConditionNode("has_escape_plan", has_escape_plan))
    escape_planning.add_child(ActionNode("work_on_goal", work_on_goal))
    survival.add_child(escape_planning)
    
    priority_root.add_child_with_priority(survival, 85.0)
    
    # Information gathering
    intel = SelectorNode("information_gathering")
    
    observe_when_safe = SequenceNode("safe_observation")
    observe_when_safe.add_child(ConditionNode("is_safe_location", is_safe_location))
    observe_when_safe.add_child(ActionNode("observe_surroundings", observe_environment))
    intel.add_child(observe_when_safe)
    
    priority_root.add_child_with_priority(intel, 60.0)
    
    # Basic needs
    needs = SelectorNode("prisoner_needs")
    rest_sequence = SequenceNode("rest_when_tired")
    rest_sequence.add_child(ConditionNode("is_tired", is_tired))
    rest_sequence.add_child(ActionNode("rest", rest))
    needs.add_child(rest_sequence)
    
    priority_root.add_child_with_priority(needs, 50.0)
    
    # Default prisoner behavior
    default_prisoner = RandomSelectorNode("default_prisoner_behavior")
    default_prisoner.add_child(ActionNode("rest", rest))
    default_prisoner.add_child(ActionNode("personal_activity", personal_activity))
    default_prisoner.add_child(ActionNode("maintain_equipment", maintain_items))
    
    priority_root.add_child_with_priority(default_prisoner, 15.0)
    
    root.add_child(priority_root)
    return root


def create_behavior_for_npc(npc: Any) -> BlackboardNode:
    """Factory method to create appropriate behavior tree for NPC"""
    
    npc_role = getattr(npc, 'role', 'prisoner')
    npc_type = getattr(npc, 'type', 'human')
    
    if npc_role == 'guard':
        return create_guard_behavior()
    elif npc_role == 'prisoner':
        return create_prisoner_behavior()
    elif npc_role in ['warden', 'admin']:
        return create_guard_behavior()  # Similar to guard but with admin duties
    else:
        return create_basic_npc_behavior(npc_role)


# Convenience function for backward compatibility
def create_basic_prisoner_behavior() -> BlackboardNode:
    """Backward compatibility function"""
    return create_prisoner_behavior()


def create_basic_guard_behavior() -> BlackboardNode:
    """Backward compatibility function"""
    return create_guard_behavior()