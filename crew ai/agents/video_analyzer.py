try:
    from crewai import Agent
    from langchain_openai import ChatOpenAI
except ImportError:
    from mock_crew import Agent
    ChatOpenAI = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

import os
import re

class VideoAnalyzerAgent:
    def __init__(self):
        if ChatOpenAI:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.3,
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.llm = None
        
    def create_agent(self):
        return Agent(
            role="Video Content Analyzer",
            goal="Analyze training videos and transcripts to assess employee engagement and comprehension",
            backstory="""You are a learning analytics expert who specializes in analyzing video content 
            and transcripts to measure learning effectiveness. You can identify key learning points, 
            assess engagement levels, and provide actionable feedback for improvement.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[]
        )
    
    def extract_youtube_id(self, url):
        """Extract YouTube video ID from URL"""
        pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def get_transcript(self, video_url):
        """Get transcript from YouTube video"""
        try:
            video_id = self.extract_youtube_id(video_url)
            if not video_id:
                return None
            
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            full_transcript = " ".join([entry['text'] for entry in transcript])
            return full_transcript
        except Exception as e:
            print(f"Error getting transcript: {e}")
            return None
    
    def analyze_transcript_prompt(self, transcript, learning_objectives=None):
        objectives_text = f"\nLearning Objectives: {learning_objectives}" if learning_objectives else ""
        
        return f"""
        Analyze the following training video transcript for learning effectiveness:
        
        Transcript: {transcript[:3000]}...  # Truncate for API limits
        {objectives_text}
        
        Provide analysis in the following areas:
        1. Key learning points covered
        2. Engagement level (1-10 scale)
        3. Comprehension difficulty (1-10 scale)
        4. Areas that might need reinforcement
        5. Overall effectiveness score (1-10)
        6. Specific recommendations for improvement
        
        Format the output as JSON:
        {{
            "key_points": ["point1", "point2", ...],
            "engagement_score": 8.5,
            "comprehension_score": 7.2,
            "areas_for_improvement": ["area1", "area2", ...],
            "effectiveness_score": 8.0,
            "recommendations": ["rec1", "rec2", ...],
            "summary": "Overall analysis summary"
        }}
        """
