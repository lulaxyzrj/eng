"""
Analytics and cognitive assessment services.
Tracks performance, analyzes patterns, and provides insights.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from ..models.game_state import GameState, GameSession, GameMove
from ..models.patient import Patient, CognitiveProfile


@dataclass
class PerformanceTrend:
    """Tracks performance trends over time."""
    metric_name: str
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)

    def add_data_point(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """Add a new data point."""
        self.values.append(value)
        self.timestamps.append(timestamp or datetime.now())

    def get_trend(self) -> str:
        """
        Determine if trend is improving, declining, or stable.

        Returns:
            'improving', 'declining', or 'stable'
        """
        if len(self.values) < 2:
            return 'stable'

        # Calculate linear regression slope (simplified)
        recent_values = self.values[-10:]  # Last 10 data points

        if len(recent_values) < 2:
            return 'stable'

        # Simple slope calculation
        n = len(recent_values)
        x = list(range(n))
        y = recent_values

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 'stable'

        slope = numerator / denominator

        # Classify trend
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'

    def get_average(self, last_n: Optional[int] = None) -> float:
        """Get average value, optionally of last N points."""
        if not self.values:
            return 0.0

        values = self.values[-last_n:] if last_n else self.values
        return sum(values) / len(values)

    def get_variance(self) -> float:
        """Get variance of the values."""
        if len(self.values) < 2:
            return 0.0
        return statistics.variance(self.values)


@dataclass
class CognitiveInsight:
    """Insight generated from cognitive data analysis."""
    insight_type: str  # strength, weakness, recommendation
    category: str  # memory, attention, speed, accuracy
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    supporting_data: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class CognitiveAnalyzer:
    """
    Analyzes cognitive performance and generates insights.
    Strategy pattern for different analysis algorithms.
    """

    def __init__(self):
        self.trends: Dict[str, PerformanceTrend] = {}

    def analyze_game_session(self, game_state: GameState) -> List[CognitiveInsight]:
        """
        Analyze a completed game session and generate insights.

        Args:
            game_state: Completed game state

        Returns:
            List of cognitive insights
        """
        insights = []

        # Analyze memory performance
        memory_insight = self._analyze_memory(game_state)
        if memory_insight:
            insights.append(memory_insight)

        # Analyze attention and focus
        attention_insight = self._analyze_attention(game_state)
        if attention_insight:
            insights.append(attention_insight)

        # Analyze response speed
        speed_insight = self._analyze_speed(game_state)
        if speed_insight:
            insights.append(speed_insight)

        # Analyze accuracy
        accuracy_insight = self._analyze_accuracy(game_state)
        if accuracy_insight:
            insights.append(accuracy_insight)

        return insights

    def _analyze_memory(self, game_state: GameState) -> Optional[CognitiveInsight]:
        """Analyze memory-specific performance."""
        metrics = game_state.metrics

        # Calculate memory strength score
        # Factors: first-attempt matches, remembering previously seen cards
        memory_score = metrics.memory_score

        if memory_score >= 80:
            return CognitiveInsight(
                insight_type='strength',
                category='memory',
                title='Excellent Memory Performance',
                description=f'Memory score of {memory_score:.1f} indicates strong recall and recognition abilities.',
                confidence=0.9,
                supporting_data={
                    'memory_score': memory_score,
                    'first_attempt_matches': metrics.first_attempt_matches
                }
            )
        elif memory_score < 50:
            return CognitiveInsight(
                insight_type='weakness',
                category='memory',
                title='Memory Improvement Opportunity',
                description=f'Memory score of {memory_score:.1f} suggests room for improvement in recall tasks.',
                confidence=0.8,
                supporting_data={
                    'memory_score': memory_score,
                    'recommendations': ['Practice with easier difficulty', 'Take breaks between sessions']
                }
            )

        return None

    def _analyze_attention(self, game_state: GameState) -> Optional[CognitiveInsight]:
        """Analyze attention and focus patterns."""
        if not game_state.move_history:
            return None

        # Analyze consistency of move times
        move_times = [m.time_taken for m in game_state.move_history]

        if len(move_times) < 3:
            return None

        # Calculate coefficient of variation (CV)
        mean_time = statistics.mean(move_times)
        std_time = statistics.stdev(move_times)
        cv = std_time / mean_time if mean_time > 0 else 0

        # Low CV indicates consistent attention
        if cv < 0.3:
            return CognitiveInsight(
                insight_type='strength',
                category='attention',
                title='Consistent Focus',
                description='Move times show consistent pacing, indicating sustained attention throughout the game.',
                confidence=0.85,
                supporting_data={
                    'coefficient_variation': cv,
                    'average_move_time': mean_time
                }
            )
        elif cv > 0.7:
            return CognitiveInsight(
                insight_type='weakness',
                category='attention',
                title='Variable Attention',
                description='Significant variation in response times may indicate fluctuating attention.',
                confidence=0.75,
                supporting_data={
                    'coefficient_variation': cv,
                    'recommendations': ['Try shorter game sessions', 'Reduce environmental distractions']
                }
            )

        return None

    def _analyze_speed(self, game_state: GameState) -> Optional[CognitiveInsight]:
        """Analyze response speed."""
        avg_time = game_state.metrics.average_move_time

        if avg_time < 2.0:
            return CognitiveInsight(
                insight_type='strength',
                category='speed',
                title='Fast Response Times',
                description=f'Average response time of {avg_time:.1f}s indicates quick decision-making.',
                confidence=0.8,
                supporting_data={'average_time': avg_time}
            )
        elif avg_time > 8.0:
            return CognitiveInsight(
                insight_type='weakness',
                category='speed',
                title='Slower Processing Speed',
                description=f'Average response time of {avg_time:.1f}s may indicate deliberate or slower processing.',
                confidence=0.75,
                supporting_data={
                    'average_time': avg_time,
                    'note': 'Slower is not necessarily worse - may indicate careful thinking'
                }
            )

        return None

    def _analyze_accuracy(self, game_state: GameState) -> Optional[CognitiveInsight]:
        """Analyze accuracy patterns."""
        accuracy = game_state.metrics.accuracy_rate

        if accuracy >= 0.85:
            return CognitiveInsight(
                insight_type='strength',
                category='accuracy',
                title='High Accuracy',
                description=f'Accuracy rate of {accuracy*100:.1f}% shows careful and precise decision-making.',
                confidence=0.9,
                supporting_data={'accuracy_rate': accuracy}
            )
        elif accuracy < 0.5:
            return CognitiveInsight(
                insight_type='recommendation',
                category='accuracy',
                title='Accuracy Enhancement',
                description=f'Accuracy rate of {accuracy*100:.1f}% could be improved with practice.',
                confidence=0.8,
                supporting_data={
                    'accuracy_rate': accuracy,
                    'recommendations': ['Take more time before selecting', 'Use the preview feature']
                }
            )

        return None

    def track_progress_over_time(self, sessions: List[GameState]) -> Dict[str, PerformanceTrend]:
        """
        Track performance trends across multiple sessions.

        Args:
            sessions: List of completed game sessions

        Returns:
            Dictionary of performance trends by metric
        """
        trends = {
            'memory_score': PerformanceTrend('memory_score'),
            'accuracy_rate': PerformanceTrend('accuracy_rate'),
            'average_move_time': PerformanceTrend('average_move_time'),
            'completion_time': PerformanceTrend('completion_time')
        }

        for session in sessions:
            timestamp = session.end_time or session.start_time or datetime.now()

            trends['memory_score'].add_data_point(
                session.metrics.memory_score, timestamp
            )
            trends['accuracy_rate'].add_data_point(
                session.metrics.accuracy_rate, timestamp
            )
            trends['average_move_time'].add_data_point(
                session.metrics.average_move_time, timestamp
            )
            trends['completion_time'].add_data_point(
                session.elapsed_time, timestamp
            )

        return trends

    def generate_progress_report(self, patient: Patient,
                                 sessions: List[GameState]) -> Dict:
        """
        Generate comprehensive progress report.

        Args:
            patient: Patient profile
            sessions: List of game sessions

        Returns:
            Progress report dictionary
        """
        if not sessions:
            return {'error': 'No sessions to analyze'}

        trends = self.track_progress_over_time(sessions)

        # Get latest insights from most recent session
        latest_insights = self.analyze_game_session(sessions[-1])

        # Calculate overall statistics
        total_games = len(sessions)
        avg_memory_score = sum(s.metrics.memory_score for s in sessions) / total_games
        avg_accuracy = sum(s.metrics.accuracy_rate for s in sessions) / total_games

        report = {
            'patient_id': patient.patient_id,
            'patient_name': patient.name,
            'report_date': datetime.now().isoformat(),
            'total_sessions': total_games,
            'date_range': {
                'first': sessions[0].start_time.isoformat() if sessions[0].start_time else None,
                'last': sessions[-1].end_time.isoformat() if sessions[-1].end_time else None
            },
            'overall_statistics': {
                'average_memory_score': avg_memory_score,
                'average_accuracy': avg_accuracy,
                'total_time_played': sum(s.elapsed_time for s in sessions)
            },
            'trends': {
                name: {
                    'current_average': trend.get_average(last_n=5),
                    'overall_average': trend.get_average(),
                    'trend_direction': trend.get_trend(),
                    'variance': trend.get_variance()
                }
                for name, trend in trends.items()
            },
            'latest_insights': [
                {
                    'type': insight.insight_type,
                    'category': insight.category,
                    'title': insight.title,
                    'description': insight.description,
                    'confidence': insight.confidence
                }
                for insight in latest_insights
            ],
            'recommendations': self._generate_recommendations(trends, latest_insights)
        }

        return report

    def _generate_recommendations(self, trends: Dict[str, PerformanceTrend],
                                 insights: List[CognitiveInsight]) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []

        # Based on trends
        memory_trend = trends.get('memory_score')
        if memory_trend and memory_trend.get_trend() == 'declining':
            recommendations.append(
                "Memory scores are declining. Consider shorter, more frequent sessions."
            )

        accuracy_trend = trends.get('accuracy_rate')
        if accuracy_trend and accuracy_trend.get_average() < 0.6:
            recommendations.append(
                "Try playing at an easier difficulty level to build confidence."
            )

        # Based on insights
        for insight in insights:
            if 'recommendations' in insight.supporting_data:
                recommendations.extend(insight.supporting_data['recommendations'])

        return recommendations


class AnalyticsService:
    """
    Main analytics service for tracking and analyzing game data.
    Facade pattern for analytics operations.
    """

    def __init__(self):
        self.analyzer = CognitiveAnalyzer()
        self._session_history: Dict[str, List[GameState]] = defaultdict(list)

    def record_session(self, patient_id: str, game_state: GameState) -> None:
        """Record a completed game session."""
        self._session_history[patient_id].append(game_state)

    def get_patient_sessions(self, patient_id: str,
                            since: Optional[datetime] = None) -> List[GameState]:
        """Get all sessions for a patient, optionally filtered by date."""
        sessions = self._session_history.get(patient_id, [])

        if since:
            sessions = [
                s for s in sessions
                if s.start_time and s.start_time >= since
            ]

        return sessions

    def analyze_session(self, game_state: GameState) -> List[CognitiveInsight]:
        """Analyze a single game session."""
        return self.analyzer.analyze_game_session(game_state)

    def get_progress_report(self, patient: Patient,
                           days: int = 30) -> Dict:
        """
        Get progress report for a patient.

        Args:
            patient: Patient profile
            days: Number of days to include in report

        Returns:
            Progress report
        """
        since = datetime.now() - timedelta(days=days)
        sessions = self.get_patient_sessions(patient.patient_id, since)

        return self.analyzer.generate_progress_report(patient, sessions)

    def compare_patients(self, patient_ids: List[str]) -> Dict:
        """
        Compare performance across multiple patients (anonymized).
        Useful for research or cohort analysis.
        """
        comparison = {
            'patient_count': len(patient_ids),
            'metrics': {}
        }

        all_scores = defaultdict(list)

        for patient_id in patient_ids:
            sessions = self._session_history.get(patient_id, [])

            for session in sessions:
                all_scores['memory_score'].append(session.metrics.memory_score)
                all_scores['accuracy_rate'].append(session.metrics.accuracy_rate)
                all_scores['average_move_time'].append(session.metrics.average_move_time)

        # Calculate statistics
        for metric, values in all_scores.items():
            if values:
                comparison['metrics'][metric] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values)
                }

        return comparison

    def get_session_summary(self, game_state: GameState) -> Dict:
        """Get a concise summary of a game session."""
        return {
            'game_id': game_state.game_id,
            'difficulty': game_state.difficulty.value,
            'completed': game_state.is_complete(),
            'duration': game_state.elapsed_time,
            'score': game_state.metrics.memory_score,
            'accuracy': game_state.metrics.accuracy_rate,
            'total_moves': game_state.metrics.total_moves,
            'hints_used': game_state.metrics.hints_used,
            'phase': game_state.phase.value
        }
