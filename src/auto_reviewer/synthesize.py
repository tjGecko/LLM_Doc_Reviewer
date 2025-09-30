"""Result synthesis and output formatting system."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import statistics

from .config import AgentsConfig, AgentReview, ReviewResults, DocumentChunk

logger = logging.getLogger(__name__)


class ResultSynthesizer:
    """Synthesizes and formats review results from multiple agents."""
    
    def __init__(self, agents_config: AgentsConfig, output_dir: Path):
        """
        Initialize the result synthesizer.
        
        Args:
            agents_config: Configuration for all agents
            output_dir: Directory to save output files
        """
        self.agents_config = agents_config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_consolidated_scores(self, agent_reviews: List[AgentReview]) -> Dict[str, float]:
        """
        Calculate consolidated scores across all agents and criteria.
        
        Args:
            agent_reviews: All agent reviews
            
        Returns:
            Dictionary of consolidated scores by criteria
        """
        if not agent_reviews:
            return {}
        
        # Collect all scores by criteria
        criteria_scores = defaultdict(list)
        
        for review in agent_reviews:
            for criterion, score in review.scores.items():
                if criterion != "error":  # Skip error scores
                    criteria_scores[criterion].append(score)
        
        # Calculate consolidated scores
        consolidated = {}
        for criterion, scores in criteria_scores.items():
            if scores:
                consolidated[criterion] = {
                    'mean': statistics.mean(scores),
                    'median': statistics.median(scores),
                    'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                    'min': min(scores),
                    'max': max(scores),
                    'count': len(scores)
                }
        
        # Also calculate simple averages for backward compatibility
        simple_consolidated = {}
        for criterion, stats in consolidated.items():
            simple_consolidated[criterion] = stats['mean']
        
        return simple_consolidated
    
    def calculate_overall_rating(self, agent_reviews: List[AgentReview]) -> float:
        """
        Calculate overall document rating.
        
        Args:
            agent_reviews: All agent reviews
            
        Returns:
            Overall rating (1-5 scale)
        """
        if not agent_reviews:
            return 0.0
        
        # Get all overall scores (excluding error reviews)
        overall_scores = [
            review.overall_score for review in agent_reviews 
            if review.overall_score > 0 and "error" not in review.scores
        ]
        
        if not overall_scores:
            return 0.0
        
        return statistics.mean(overall_scores)
    
    def generate_paragraph_summary(self, agent_reviews: List[AgentReview]) -> Dict[str, Any]:
        """
        Generate summary statistics by paragraph.
        
        Args:
            agent_reviews: All agent reviews
            
        Returns:
            Dictionary with paragraph summaries
        """
        paragraph_data = defaultdict(list)
        
        # Group reviews by paragraph
        for review in agent_reviews:
            if "error" not in review.scores:  # Skip error reviews
                paragraph_data[review.paragraph_id].append(review)
        
        # Generate summaries
        paragraph_summaries = {}
        for paragraph_id, reviews in paragraph_data.items():
            if not reviews:
                continue
            
            scores = [r.overall_score for r in reviews]
            confidences = [r.confidence for r in reviews]
            
            # Count suggestions
            suggestions = [r.suggested_rewrite for r in reviews if r.suggested_rewrite]
            
            paragraph_summaries[paragraph_id] = {
                'agent_count': len(reviews),
                'avg_score': statistics.mean(scores),
                'score_range': [min(scores), max(scores)],
                'avg_confidence': statistics.mean(confidences),
                'has_suggestions': len(suggestions) > 0,
                'suggestion_count': len(suggestions),
                'agents_reviewed': [r.agent_name for r in reviews]
            }
        
        return paragraph_summaries
    
    def generate_agent_summary(self, agent_reviews: List[AgentReview]) -> Dict[str, Any]:
        """
        Generate summary statistics by agent.
        
        Args:
            agent_reviews: All agent reviews
            
        Returns:
            Dictionary with agent summaries
        """
        agent_data = defaultdict(list)
        
        # Group reviews by agent
        for review in agent_reviews:
            if "error" not in review.scores:  # Skip error reviews
                agent_data[review.agent_name].append(review)
        
        # Generate summaries
        agent_summaries = {}
        for agent_name, reviews in agent_data.items():
            if not reviews:
                continue
            
            scores = [r.overall_score for r in reviews]
            confidences = [r.confidence for r in reviews]
            
            # Analyze scoring patterns
            high_scores = sum(1 for s in scores if s >= 4.0)
            low_scores = sum(1 for s in scores if s <= 2.0)
            
            # Count criteria usage
            all_criteria = []
            for review in reviews:
                all_criteria.extend(review.scores.keys())
            criteria_usage = Counter(all_criteria)
            
            agent_summaries[agent_name] = {
                'review_count': len(reviews),
                'avg_score': statistics.mean(scores),
                'score_std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0,
                'avg_confidence': statistics.mean(confidences),
                'high_scores': high_scores,
                'low_scores': low_scores,
                'most_used_criteria': criteria_usage.most_common(3),
                'paragraphs_reviewed': len(set(r.paragraph_id for r in reviews))
            }
        
        return agent_summaries
    
    def save_results(self, results: ReviewResults):
        """
        Save results to multiple output formats.
        
        Args:
            results: Complete review results
        """
        logger.info(f"Saving results to {self.output_dir}")
        
        # Generate summaries
        paragraph_summary = self.generate_paragraph_summary(results.agent_reviews)
        agent_summary = self.generate_agent_summary(results.agent_reviews)
        
        # Save main results JSON
        self._save_main_results(results, paragraph_summary, agent_summary)
        
        # Save per-agent JSONL files
        self._save_agent_jsonl_files(results.agent_reviews)
        
        # Save per-agent markdown reports
        self._save_agent_markdown_reports(results.agent_reviews)
        
        # Save consolidated summary
        self._save_consolidated_summary(results, paragraph_summary, agent_summary)
        
        # Save human-readable report
        self._save_human_readable_report(results, paragraph_summary, agent_summary)
        
        logger.info("All result files saved successfully")
    
    def _save_main_results(self, results: ReviewResults, paragraph_summary: Dict, agent_summary: Dict):
        """Save the main results JSON file."""
        output_path = self.output_dir / "run.json"
        
        main_data = {
            'metadata': {
                'document_path': results.document_path,
                'run_timestamp': results.run_timestamp,
                'agents_used': results.agents_used,
                'total_paragraphs': results.total_paragraphs,
                'total_reviews': len(results.agent_reviews),
                'overall_rating': results.overall_rating
            },
            'consolidated_scores': results.consolidated_scores,
            'paragraph_summary': paragraph_summary,
            'agent_summary': agent_summary,
            'raw_reviews': [review.dict() for review in results.agent_reviews]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved main results to {output_path}")
    
    def _save_agent_jsonl_files(self, agent_reviews: List[AgentReview]):
        """Save per-agent JSONL files."""
        agent_data = defaultdict(list)
        
        # Group by agent
        for review in agent_reviews:
            agent_data[review.agent_name].append(review)
        
        # Save each agent's reviews
        for agent_name, reviews in agent_data.items():
            # Clean agent name for filename
            safe_name = "".join(c for c in agent_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            output_path = self.output_dir / f"{safe_name}.jsonl"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for review in reviews:
                    json.dump(review.dict(), f, ensure_ascii=False)
                    f.write('\n')
            
            logger.info(f"Saved {len(reviews)} reviews for {agent_name} to {output_path}")
    
    def _save_agent_markdown_reports(self, agent_reviews: List[AgentReview]):
        """Save per-agent markdown reports."""
        agent_data = defaultdict(list)
        
        # Group by agent
        for review in agent_reviews:
            agent_data[review.agent_name].append(review)
        
        # Save each agent's markdown report
        for agent_name, reviews in agent_data.items():
            # Clean agent name for filename
            safe_name = "".join(c for c in agent_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            output_path = self.output_dir / f"{safe_name}.md"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                self._write_agent_markdown_report(f, agent_name, reviews)
            
            logger.info(f"Saved markdown report for {agent_name} to {output_path}")
    
    def _write_agent_markdown_report(self, f, agent_name: str, reviews: List[AgentReview]):
        """Write a markdown report for a single agent."""
        # Header
        f.write(f"# {agent_name} Review Report\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n")
        f.write(f"**Total Reviews**: {len(reviews)}\n\n")
        
        # Summary statistics
        if reviews:
            scores = [r.overall_score for r in reviews if r.overall_score > 0]
            if scores:
                f.write("## Summary Statistics\n\n")
                f.write(f"- **Average Score**: {statistics.mean(scores):.2f}\n")
                f.write(f"- **Score Range**: {min(scores):.1f} - {max(scores):.1f}\n")
                f.write(f"- **Standard Deviation**: {statistics.stdev(scores) if len(scores) > 1 else 0:.2f}\n")
                
                # Confidence statistics
                confidences = [r.confidence for r in reviews]
                f.write(f"- **Average Confidence**: {statistics.mean(confidences):.2f}\n\n")
        
        # Individual reviews
        f.write("## Individual Reviews\n\n")
        
        for i, review in enumerate(reviews, 1):
            f.write(f"### Review {i}: {review.paragraph_id}\n\n")
            f.write(f"**Overall Score**: {review.overall_score:.2f}\n")
            f.write(f"**Confidence**: {review.confidence:.2f}\n\n")
            
            # Individual scores
            if review.scores and "error" not in review.scores:
                f.write("**Detailed Scores**:\n")
                for criterion, score in review.scores.items():
                    f.write(f"- {criterion}: {score:.1f}\n")
                f.write("\n")
            
            # Comments
            f.write("**Comments**:\n")
            f.write(f"{review.comments}\n\n")
            
            # Suggested rewrite
            if review.suggested_rewrite:
                f.write("**Suggested Rewrite**:\n")
                f.write(f"> {review.suggested_rewrite}\n\n")
            
            f.write("---\n\n")
    
    def _save_consolidated_summary(self, results: ReviewResults, paragraph_summary: Dict, agent_summary: Dict):
        """Save consolidated summary JSON."""
        output_path = self.output_dir / "consolidated.json"
        
        summary_data = {
            'document_metadata': {
                'path': results.document_path,
                'timestamp': results.run_timestamp,
                'total_paragraphs': results.total_paragraphs,
                'overall_rating': results.overall_rating
            },
            'agent_performance': agent_summary,
            'paragraph_analysis': paragraph_summary,
            'consolidated_scores': results.consolidated_scores,
            'recommendations': self._generate_recommendations(results, agent_summary)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved consolidated summary to {output_path}")
    
    def _save_human_readable_report(self, results: ReviewResults, paragraph_summary: Dict, agent_summary: Dict):
        """Save a human-readable markdown report."""
        output_path = self.output_dir / "review_report.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            self._write_human_readable_report(f, results, paragraph_summary, agent_summary)
        
        logger.info(f"Saved human-readable report to {output_path}")
    
    def _write_human_readable_report(self, f, results: ReviewResults, paragraph_summary: Dict, agent_summary: Dict):
        """Write a comprehensive human-readable report."""
        f.write("# Document Review Report\n\n")
        
        # Overview
        f.write("## Overview\n\n")
        f.write(f"- **Document**: {Path(results.document_path).name}\n")
        f.write(f"- **Review Date**: {datetime.fromisoformat(results.run_timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Overall Rating**: {results.overall_rating:.2f}/5.0\n")
        f.write(f"- **Paragraphs Reviewed**: {results.total_paragraphs}\n")
        f.write(f"- **Total Reviews**: {len(results.agent_reviews)}\n")
        f.write(f"- **Agents Used**: {', '.join(results.agents_used)}\n\n")
        
        # Key Findings
        f.write("## Key Findings\n\n")
        
        # Overall assessment
        if results.overall_rating >= 4.0:
            f.write("✅ **Document Quality**: Excellent - The document meets high standards across most criteria.\n")
        elif results.overall_rating >= 3.0:
            f.write("⚠️ **Document Quality**: Good - The document is solid but has areas for improvement.\n")
        elif results.overall_rating >= 2.0:
            f.write("⚠️ **Document Quality**: Fair - The document needs significant improvements.\n")
        else:
            f.write("❌ **Document Quality**: Poor - The document requires major revisions.\n")
        f.write("\n")
        
        # Agent performance summary
        f.write("### Agent Performance Summary\n\n")
        for agent_name, summary in agent_summary.items():
            f.write(f"- **{agent_name}**: ")
            f.write(f"{summary['review_count']} reviews, ")
            f.write(f"avg score: {summary['avg_score']:.2f}, ")
            f.write(f"confidence: {summary['avg_confidence']:.2f}\n")
        f.write("\n")
        
        # Consolidated scores
        if results.consolidated_scores:
            f.write("### Scores by Criteria\n\n")
            for criterion, score in sorted(results.consolidated_scores.items()):
                f.write(f"- **{criterion}**: {score:.2f}/5.0\n")
            f.write("\n")
        
        # Recommendations
        recommendations = self._generate_recommendations(results, agent_summary)
        if recommendations:
            f.write("## Recommendations\n\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")
        
        # Paragraph-level insights
        if paragraph_summary:
            f.write("## Paragraph-level Analysis\n\n")
            
            # Find problematic paragraphs
            low_scoring = {pid: data for pid, data in paragraph_summary.items() if data['avg_score'] < 3.0}
            high_scoring = {pid: data for pid, data in paragraph_summary.items() if data['avg_score'] >= 4.0}
            
            if low_scoring:
                f.write("### Paragraphs Needing Attention\n\n")
                for pid, data in sorted(low_scoring.items(), key=lambda x: x[1]['avg_score']):
                    f.write(f"- **{pid}**: Score {data['avg_score']:.2f} ")
                    f.write(f"({data['agent_count']} agents reviewed)\n")
                f.write("\n")
            
            if high_scoring:
                f.write("### Strong Paragraphs\n\n")
                for pid, data in sorted(high_scoring.items(), key=lambda x: x[1]['avg_score'], reverse=True)[:5]:
                    f.write(f"- **{pid}**: Score {data['avg_score']:.2f} ")
                    f.write(f"({data['agent_count']} agents reviewed)\n")
                f.write("\n")
    
    def _generate_recommendations(self, results: ReviewResults, agent_summary: Dict) -> List[str]:
        """Generate actionable recommendations based on results."""
        recommendations = []
        
        # Overall quality recommendations
        if results.overall_rating < 3.0:
            recommendations.append("Consider comprehensive revision focusing on the lowest-scoring criteria")
        elif results.overall_rating < 4.0:
            recommendations.append("Document is good but could benefit from targeted improvements")
        
        # Criteria-specific recommendations
        if results.consolidated_scores:
            low_scoring_criteria = {k: v for k, v in results.consolidated_scores.items() if v < 3.0}
            if low_scoring_criteria:
                worst_criterion = min(low_scoring_criteria.items(), key=lambda x: x[1])
                recommendations.append(f"Priority: Address issues with '{worst_criterion[0]}' (score: {worst_criterion[1]:.2f})")
        
        # Agent consensus recommendations
        agent_scores = []
        for agent_name, summary in agent_summary.items():
            agent_scores.append((agent_name, summary['avg_score']))
        
        if agent_scores:
            agent_scores.sort(key=lambda x: x[1])
            if agent_scores[0][1] < 2.5:
                recommendations.append(f"The {agent_scores[0][0]} raised significant concerns - review their specific feedback")
        
        # High-confidence, low-score recommendations
        low_conf_high_impact = []
        for review in results.agent_reviews:
            if review.confidence >= 0.8 and review.overall_score <= 2.0:
                low_conf_high_impact.append(review)
        
        if low_conf_high_impact:
            recommendations.append("Several high-confidence agents identified serious issues - prioritize addressing these")
        
        return recommendations
    
    def generate_rewrite_synthesis(self, agent_reviews: List[AgentReview]) -> Dict[str, str]:
        """Generate synthesized rewrites by combining agent suggestions.
        
        Args:
            agent_reviews: All agent reviews
            
        Returns:
            Dictionary mapping paragraph IDs to synthesized rewrites
        """
        paragraph_rewrites = defaultdict(list)
        
        # Group rewrites by paragraph
        for review in agent_reviews:
            if review.rewritten_text and review.rewritten_text.strip():
                paragraph_rewrites[review.paragraph_number].append({
                    'agent': review.agent_name,
                    'text': review.rewritten_text,
                    'score': review.overall_score,
                    'confidence': review.confidence
                })
        
        # Synthesize rewrites for each paragraph
        synthesized = {}
        for paragraph_id, rewrites in paragraph_rewrites.items():
            if len(rewrites) == 1:
                # Single rewrite - use as is
                synthesized[paragraph_id] = rewrites[0]['text']
            else:
                # Multiple rewrites - synthesize based on confidence and scores
                best_rewrite = max(rewrites, key=lambda x: x['confidence'] * x['score'])
                synthesized[paragraph_id] = best_rewrite['text']
                
                # Add note about multiple suggestions
                agent_names = [r['agent'] for r in rewrites]
                synthesized[f"{paragraph_id}_note"] = f"Multiple rewrites suggested by: {', '.join(agent_names)}"
        
        return synthesized
    
    def generate_comment_categories(self, agent_reviews: List[AgentReview]) -> Dict[str, List[str]]:
        """Categorize and aggregate comments from all agents.
        
        Args:
            agent_reviews: All agent reviews
            
        Returns:
            Dictionary of categorized comments
        """
        categories = {
            'clarity_issues': [],
            'technical_concerns': [],
            'structure_feedback': [],
            'content_suggestions': [],
            'positive_feedback': [],
            'general_comments': []
        }
        
        # Keywords for categorization
        category_keywords = {
            'clarity_issues': ['unclear', 'confusing', 'ambiguous', 'vague', 'complex'],
            'technical_concerns': ['error', 'incorrect', 'inaccurate', 'missing', 'wrong'],
            'structure_feedback': ['organization', 'structure', 'flow', 'order', 'sequence'],
            'content_suggestions': ['add', 'include', 'expand', 'detail', 'example'],
            'positive_feedback': ['good', 'excellent', 'clear', 'well', 'strong']
        }
        
        for review in agent_reviews:
            if not review.comments:
                continue
                
            comment = review.comments.lower()
            categorized = False
            
            # Try to categorize based on keywords
            for category, keywords in category_keywords.items():
                if any(keyword in comment for keyword in keywords):
                    categories[category].append({
                        'agent': review.agent_name,
                        'paragraph': review.paragraph_number,
                        'comment': review.comments,
                        'score': review.overall_score
                    })
                    categorized = True
                    break
            
            # If not categorized, put in general
            if not categorized:
                categories['general_comments'].append({
                    'agent': review.agent_name,
                    'paragraph': review.paragraph_number,
                    'comment': review.comments,
                    'score': review.overall_score
                })
        
        return categories
    
    def calculate_weighted_scores(self, agent_reviews: List[AgentReview], agent_weights: Dict[str, float] = None) -> Dict[str, float]:
        """Calculate weighted consolidated scores based on agent expertise.
        
        Args:
            agent_reviews: All agent reviews
            agent_weights: Optional weights for different agents
            
        Returns:
            Dictionary of weighted consolidated scores
        """
        if not agent_weights:
            # Equal weights for all agents
            unique_agents = set(review.agent_name for review in agent_reviews)
            agent_weights = {agent: 1.0 for agent in unique_agents}
        
        # Collect weighted scores by criteria
        weighted_criteria_scores = defaultdict(list)
        
        for review in agent_reviews:
            weight = agent_weights.get(review.agent_name, 1.0)
            
            # Weight by agent confidence as well
            total_weight = weight * review.confidence
            
            # Add overall score
            weighted_criteria_scores['overall'].append((review.overall_score, total_weight))
            
            # Add individual criteria scores if available
            if hasattr(review, 'scores') and review.scores:
                for criterion, score in review.scores.items():
                    if criterion != "error":
                        weighted_criteria_scores[criterion].append((score, total_weight))
        
        # Calculate weighted averages
        weighted_scores = {}
        for criterion, score_weight_pairs in weighted_criteria_scores.items():
            if score_weight_pairs:
                total_weighted_score = sum(score * weight for score, weight in score_weight_pairs)
                total_weight = sum(weight for _, weight in score_weight_pairs)
                
                if total_weight > 0:
                    weighted_scores[criterion] = total_weighted_score / total_weight
        
        return weighted_scores
