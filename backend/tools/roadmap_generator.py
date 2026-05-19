"""
Smart Study Assistant Roadmap Generator
Creates personalized learning roadmaps for subjects
"""
import json
import os
from typing import Dict, List, Any, Optional
from .ai_summarizer import AISummarizer

class RoadmapGenerator:
    """Generates structured learning roadmaps"""
    
    def __init__(self):
        self.ai_summarizer = AISummarizer()
    
    def generate_roadmap(self, subject: str, user_level: str = "beginner", 
                        goals: List[str] = None, timeframe: str = "3 months") -> Dict[str, Any]:
        """
        Generate a comprehensive learning roadmap
        
        Args:
            subject: Subject to learn (e.g., "React", "Python", "Data Science")
            user_level: Current skill level (beginner, intermediate, advanced)
            goals: Specific learning goals
            timeframe: Desired completion timeframe
            
        Returns:
            Structured roadmap with learning phases and milestones
        """
        try:
            prompt = self._create_roadmap_prompt(subject, user_level, goals, timeframe)
            
            response = self.ai_summarizer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert educational curriculum designer. Create comprehensive, structured learning roadmaps."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            roadmap_content = response.choices[0].message.content.strip()
            
            # Parse the roadmap content
            roadmap_data = self._parse_roadmap_content(roadmap_content)
            
            return {
                'success': True,
                'subject': subject,
                'user_level': user_level,
                'timeframe': timeframe,
                'roadmap': roadmap_data,
                'total_phases': len(roadmap_data.get('phases', [])),
                'estimated_completion_time': self._calculate_total_time(roadmap_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Roadmap generation failed: {str(e)}",
                'roadmap': self._create_fallback_roadmap(subject)
            }
    
    def _create_roadmap_prompt(self, subject: str, user_level: str, 
                              goals: List[str], timeframe: str) -> str:
        """Create prompt for roadmap generation"""
        
        goals_text = "\n".join([f"- {goal}" for goal in goals]) if goals else "- Become proficient in the subject"
        
        level_descriptions = {
            "beginner": "no prior experience, starting from scratch",
            "intermediate": "some basic knowledge, understand fundamentals",
            "advanced": "strong foundation, looking to master advanced topics"
        }
        
        prompt = f"""
Create a comprehensive learning roadmap for {subject}.

Student Profile:
- Current Level: {user_level} ({level_descriptions.get(user_level, '')})
- Learning Goals:
{goals_text}
- Target Timeframe: {timeframe}

Requirements:
1. Break down into logical phases (beginner to advanced)
2. Each phase should have specific topics and subtopics
3. Include practical projects/exercises for each phase
4. Estimate time for each phase
5. Include milestones and check-points
6. Suggest resources for each topic (books, tutorials, videos)
7. Include assessment methods to track progress

Format your response as JSON:
{{
    "title": "Learning Roadmap: {subject}",
    "description": "Brief overview of this learning journey",
    "prerequisites": ["List of prerequisites if any"],
    "phases": [
        {{
            "phase": 1,
            "title": "Phase Title",
            "description": "What this phase covers",
            "duration_weeks": 4,
            "topics": [
                {{
                    "topic": "Topic Name",
                    "description": "What to learn",
                    "resources": ["Resource 1", "Resource 2"],
                    "practice": ["Exercise 1", "Exercise 2"],
                    "estimated_hours": 10
                }}
            ],
            "milestone": "What you'll accomplish",
            "assessment": "How to test your knowledge"
        }}
    ],
    "final_project": "Capstone project description",
    "next_steps": ["What to learn after this roadmap"]
}}

Make the roadmap practical, achievable, and comprehensive.
"""
        return prompt
    
    def _parse_roadmap_content(self, roadmap_content: str) -> Dict:
        """Parse AI-generated roadmap content"""
        try:
            # Try to extract JSON from the response
            if "```json" in roadmap_content:
                json_start = roadmap_content.find("```json") + 7
                json_end = roadmap_content.find("```", json_start)
                json_content = roadmap_content[json_start:json_end].strip()
            elif "{" in roadmap_content and "}" in roadmap_content:
                json_start = roadmap_content.find("{")
                json_end = roadmap_content.rfind("}") + 1
                json_content = roadmap_content[json_start:json_end].strip()
            else:
                raise ValueError("No JSON found in response")
            
            roadmap_data = json.loads(json_content)
            
            # Validate and clean the data
            if 'phases' not in roadmap_data:
                roadmap_data['phases'] = []
            
            # Ensure each phase has required fields
            for i, phase in enumerate(roadmap_data['phases']):
                phase.setdefault('phase', i + 1)
                phase.setdefault('duration_weeks', 4)
                phase.setdefault('topics', [])
                phase.setdefault('milestone', f"Complete Phase {i + 1}")
                phase.setdefault('assessment', 'Self-assessment quiz')
            
            return roadmap_data
            
        except Exception as e:
            # Fallback: create basic roadmap structure
            return self._create_fallback_roadmap("Subject")
    
    def _create_fallback_roadmap(self, subject: str) -> Dict:
        """Create basic fallback roadmap if AI generation fails"""
        return {
            'title': f'Learning Roadmap: {subject}',
            'description': f'A structured approach to learning {subject}',
            'prerequisites': ['Basic computer skills'],
            'phases': [
                {
                    'phase': 1,
                    'title': 'Fundamentals',
                    'description': 'Learn the basics',
                    'duration_weeks': 4,
                    'topics': [
                        {
                            'topic': 'Introduction',
                            'description': 'Getting started',
                            'resources': ['Online tutorials'],
                            'practice': ['Basic exercises'],
                            'estimated_hours': 10
                        }
                    ],
                    'milestone': 'Understand basic concepts',
                    'assessment': 'Complete basic exercises'
                }
            ],
            'final_project': 'Apply your knowledge',
            'next_steps': ['Advanced topics']
        }
    
    def _calculate_total_time(self, roadmap_data: Dict) -> str:
        """Calculate total estimated completion time"""
        total_weeks = sum(phase.get('duration_weeks', 4) for phase in roadmap_data.get('phases', []))
        total_hours = 0
        
        for phase in roadmap_data.get('phases', []):
            for topic in phase.get('topics', []):
                total_hours += topic.get('estimated_hours', 0)
        
        return f"{total_weeks} weeks, {total_hours} hours"
    
    def update_roadmap_progress(self, roadmap: Dict, completed_topics: List[str], 
                              current_phase: int) -> Dict:
        """
        Update roadmap with user progress
        
        Args:
            roadmap: Original roadmap data
            completed_topics: List of completed topic names
            current_phase: Current active phase number
            
        Returns:
            Updated roadmap with progress information
        """
        updated_roadmap = roadmap.copy()
        
        # Mark completed topics
        for phase in updated_roadmap.get('phases', []):
            for topic in phase.get('topics', []):
                if topic['topic'] in completed_topics:
                    topic['completed'] = True
                else:
                    topic['completed'] = False
        
        # Set current phase
        updated_roadmap['current_phase'] = current_phase
        
        # Calculate progress percentage
        total_topics = sum(len(phase.get('topics', [])) for phase in updated_roadmap.get('phases', []))
        completed_count = len(completed_topics)
        progress_percentage = (completed_count / total_topics * 100) if total_topics > 0 else 0
        
        updated_roadmap['progress_percentage'] = progress_percentage
        
        # Determine next milestone
        next_milestone = None
        for phase in updated_roadmap.get('phases', []):
            if phase['phase'] >= current_phase:
                next_milestone = phase.get('milestone', f'Complete Phase {phase["phase"]}')
                break
        
        updated_roadmap['next_milestone'] = next_milestone
        
        return updated_roadmap
    
    def get_next_recommendations(self, roadmap: Dict, user_progress: Dict) -> List[Dict]:
        """
        Get recommendations for next learning steps
        
        Args:
            roadmap: Learning roadmap
            user_progress: User's current progress
            
        Returns:
            List of recommended next steps
        """
        recommendations = []
        current_phase = user_progress.get('current_phase', 1)
        completed_topics = user_progress.get('completed_topics', [])
        
        # Find current phase in roadmap
        current_phase_data = None
        for phase in roadmap.get('phases', []):
            if phase['phase'] == current_phase:
                current_phase_data = phase
                break
        
        if current_phase_data:
            # Recommend incomplete topics in current phase
            for topic in current_phase_data.get('topics', []):
                if topic['topic'] not in completed_topics:
                    recommendations.append({
                        'type': 'topic',
                        'title': topic['topic'],
                        'description': topic['description'],
                        'estimated_hours': topic.get('estimated_hours', 5),
                        'priority': 'high',
                        'phase': current_phase
                    })
            
            # If all topics in current phase are complete, recommend next phase
            phase_topics = [t['topic'] for t in current_phase_data.get('topics', [])]
            if all(topic in completed_topics for topic in phase_topics):
                next_phase = current_phase + 1
                for phase in roadmap.get('phases', []):
                    if phase['phase'] == next_phase:
                        recommendations.append({
                            'type': 'phase',
                            'title': f"Start {phase['title']}",
                            'description': phase['description'],
                            'estimated_hours': sum(t.get('estimated_hours', 5) for t in phase.get('topics', [])),
                            'priority': 'medium',
                            'phase': next_phase
                        })
                        break
        
        # If no specific recommendations, suggest review
        if not recommendations:
            recommendations.append({
                'type': 'review',
                'title': 'Review and Practice',
                'description': 'Review completed topics and work on practice exercises',
                'estimated_hours': 10,
                'priority': 'low',
                'phase': current_phase
            })
        
        return recommendations
    
    def generate_micro_roadmap(self, subject: str, specific_topic: str, 
                             duration_days: int = 7) -> Dict:
        """
        Generate a focused micro-roadmap for a specific topic
        
        Args:
            subject: Main subject area
            specific_topic: Specific topic to focus on
            duration_days: Duration in days
            
        Returns:
            Focused learning plan for the specific topic
        """
        try:
            prompt = f"""
Create a focused learning plan for mastering: {specific_topic} (part of {subject})

Duration: {duration_days} days
Goal: Deep understanding and practical application of {specific_topic}

Create a day-by-day plan with:
- Daily learning objectives
- Specific topics to cover
- Practice exercises
- Resources for each day
- Small assessments

Format as JSON:
{{
    "topic": "{specific_topic}",
    "subject": "{subject}",
    "duration_days": {duration_days},
    "daily_plan": [
        {{
            "day": 1,
            "title": "Day 1 Title",
            "objectives": ["Objective 1", "Objective 2"],
            "topics": ["Topic 1", "Topic 2"],
            "resources": ["Resource 1", "Resource 2"],
            "exercises": ["Exercise 1"],
            "assessment": "How to check understanding"
        }}
    ],
    "final_assessment": "Capstone exercise",
    "prerequisites": ["Needed knowledge"]
}}
"""
            
            response = self.ai_summarizer.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert tutor creating focused learning plans."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            else:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_content = content[json_start:json_end].strip()
            
            micro_roadmap = json.loads(json_content)
            
            return {
                'success': True,
                'micro_roadmap': micro_roadmap
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Micro-roadmap generation failed: {str(e)}"
            }
