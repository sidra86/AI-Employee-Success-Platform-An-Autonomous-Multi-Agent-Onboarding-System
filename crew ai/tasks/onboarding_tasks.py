try:
    from crewai import Task
except ImportError:
    from mock_crew import Task
import json

class OnboardingTasks:
    
    @staticmethod
    def quiz_generation_task(agent, topic, difficulty="medium", num_questions=10):
        return Task(
            description=f"""
            Generate a comprehensive quiz for the onboarding topic: {topic}
            
            Requirements:
            - Difficulty: {difficulty}
            - Number of questions: {num_questions}
            - Mix of question types (multiple choice, true/false, short answer)
            - Include correct answers and explanations
            - Focus on practical application and company-specific scenarios
            
            The quiz should test both theoretical knowledge and practical application
            relevant to the employee's role and company policies.
            """,
            agent=agent,
            expected_output="A well-structured quiz in JSON format with questions, answers, and explanations"
        )
    
    @staticmethod
    def video_analysis_task(agent, video_url, learning_objectives=None):
        return Task(
            description=f"""
            Analyze the training video at: {video_url}
            
            Tasks:
            1. Extract and analyze the video transcript
            2. Assess the content quality and engagement level
            3. Identify key learning points covered
            4. Evaluate comprehension difficulty
            5. Provide recommendations for improvement
            
            Learning Objectives: {learning_objectives or 'General onboarding content'}
            
            Focus on how well the video content aligns with learning objectives
            and its effectiveness for employee onboarding.
            """,
            agent=agent,
            expected_output="Detailed video analysis with engagement scores, key points, and recommendations in JSON format"
        )
    
    @staticmethod
    def progress_tracking_task(agent, employee_id, quiz_data, video_data):
        return Task(
            description=f"""
            Generate a comprehensive progress report for employee ID: {employee_id}
            
            Data to analyze:
            - Quiz performance data: {quiz_data}
            - Video engagement data: {video_data}
            
            Analysis should include:
            1. Overall progress calculation
            2. Learning velocity assessment
            3. Strength and weakness identification
            4. Risk factor analysis
            5. Completion timeline prediction
            6. Personalized recommendations
            
            Provide actionable insights for both the employee and HR team.
            """,
            agent=agent,
            expected_output="Comprehensive progress report with metrics, insights, and recommendations in JSON format"
        )
    
    @staticmethod
    def feedback_generation_task(agent, employee_data, performance_summary):
        return Task(
            description=f"""
            Generate personalized feedback for the employee based on their onboarding performance.
            
            Employee Information: {employee_data}
            Performance Summary: {performance_summary}
            
            Create feedback that:
            1. Celebrates achievements and strengths
            2. Addresses areas for improvement constructively
            3. Provides specific, actionable next steps
            4. Maintains motivation and engagement
            5. Sets realistic expectations and timelines
            
            The feedback should be professional, supportive, and tailored to the individual's
            learning style and performance patterns.
            """,
            agent=agent,
            expected_output="Personalized feedback message with specific recommendations and encouragement in JSON format"
        )
    
    @staticmethod
    def onboarding_orchestration_task(agent, employee_data):
        return Task(
            description=f"""
            Orchestrate the complete onboarding process for: {employee_data}
            
            Coordinate the following workflow:
            1. Generate appropriate quizzes based on role and department
            2. Analyze training video engagement
            3. Track overall progress and learning velocity
            4. Generate personalized feedback and recommendations
            5. Create action plan for completion
            
            Ensure all components work together to provide a cohesive
            onboarding experience tailored to the employee's needs.
            """,
            agent=agent,
            expected_output="Complete onboarding workflow results with all components integrated"
        )
