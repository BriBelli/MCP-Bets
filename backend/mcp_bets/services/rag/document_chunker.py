"""
Document Chunking Service for RAG Knowledge Base

Breaks down NFL data into optimal-sized chunks (500-800 tokens) for embedding.
Implements sliding window with overlap for context preservation.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import tiktoken

from mcp_bets.models.player import Player
from mcp_bets.models.game import Game
from mcp_bets.models.injury import Injury
from mcp_bets.models.player_game_stats import PlayerGameStats
from mcp_bets.models.player_prop import PlayerProp


class DocumentChunk:
    """Represents a single document chunk with metadata"""
    
    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        token_count: int
    ):
        self.content = content
        self.metadata = metadata
        self.token_count = token_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            "document_chunk": self.content,
            "meta": self.metadata
        }


class DocumentChunker:
    """
    Chunks NFL data into embedding-ready documents
    
    Target: 500-800 tokens per chunk
    Overlap: 50-100 tokens between chunks
    """
    
    def __init__(
        self,
        target_chunk_size: int = 650,  # tokens
        chunk_overlap: int = 75,  # tokens
        min_chunk_size: int = 500,
        max_chunk_size: int = 800
    ):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Initialize tiktoken for GPT tokenization (matches OpenAI embeddings)
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.tokenizer.encode(text))
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for intelligent chunking"""
        # Use regex to split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_chunks_from_text(
        self,
        text: str,
        base_metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """
        Split long text into chunks with overlap
        
        Args:
            text: Input text to chunk
            base_metadata: Metadata to attach to all chunks
            
        Returns:
            List of DocumentChunk objects
        """
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If single sentence exceeds max, split it further
            if sentence_tokens > self.max_chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(DocumentChunk(
                        content=chunk_text,
                        metadata={**base_metadata, "chunk_index": len(chunks)},
                        token_count=current_tokens
                    ))
                    current_chunk = []
                    current_tokens = 0
                
                # Split long sentence by words
                words = sentence.split()
                temp_chunk = []
                temp_tokens = 0
                
                for word in words:
                    word_tokens = self.count_tokens(word + " ")
                    if temp_tokens + word_tokens > self.target_chunk_size:
                        chunk_text = " ".join(temp_chunk)
                        chunks.append(DocumentChunk(
                            content=chunk_text,
                            metadata={**base_metadata, "chunk_index": len(chunks)},
                            token_count=temp_tokens
                        ))
                        temp_chunk = []
                        temp_tokens = 0
                    
                    temp_chunk.append(word)
                    temp_tokens += word_tokens
                
                if temp_chunk:
                    current_chunk = temp_chunk
                    current_tokens = temp_tokens
                
                continue
            
            # Check if adding sentence exceeds target
            if current_tokens + sentence_tokens > self.target_chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append(DocumentChunk(
                        content=chunk_text,
                        metadata={**base_metadata, "chunk_index": len(chunks)},
                        token_count=current_tokens
                    ))
                
                # Start new chunk with overlap
                if chunks and self.chunk_overlap > 0:
                    # Include last few sentences for context
                    overlap_sentences = []
                    overlap_tokens = 0
                    
                    for prev_sent in reversed(current_chunk):
                        sent_tokens = self.count_tokens(prev_sent)
                        if overlap_tokens + sent_tokens <= self.chunk_overlap:
                            overlap_sentences.insert(0, prev_sent)
                            overlap_tokens += sent_tokens
                        else:
                            break
                    
                    current_chunk = overlap_sentences + [sentence]
                    current_tokens = overlap_tokens + sentence_tokens
                else:
                    current_chunk = [sentence]
                    current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(DocumentChunk(
                content=chunk_text,
                metadata={**base_metadata, "chunk_index": len(chunks)},
                token_count=current_tokens
            ))
        
        return chunks
    
    def chunk_player_profile(
        self,
        player: Player,
        season: int,
        recent_stats: Optional[List[PlayerGameStats]] = None
    ) -> List[DocumentChunk]:
        """
        Create chunks from player profile data
        
        Args:
            player: Player model instance
            season: Current season year
            recent_stats: Optional recent game stats
            
        Returns:
            List of DocumentChunk objects
        """
        # Build comprehensive player profile text
        profile_parts = [
            f"Player Profile: {player.first_name} {player.last_name}",
            f"Position: {player.position}",
            f"Team: {player.team.name if player.team else 'Free Agent'}",
            f"Jersey Number: #{player.jersey_number}" if player.jersey_number else "",
            f"Status: {player.status}" if player.status else "Active",
        ]
        
        if player.height and player.weight:
            profile_parts.append(f"Physical: {player.height}, {player.weight} lbs")
        
        if player.college:
            profile_parts.append(f"College: {player.college}")
        
        # Add recent performance if available
        if recent_stats:
            profile_parts.append("\nRecent Performance:")
            for stat in recent_stats[:5]:  # Last 5 games
                stat_summary = self._format_game_stats(stat, player.position)
                profile_parts.append(stat_summary)
        
        profile_text = "\n".join([p for p in profile_parts if p])
        
        # Base metadata
        base_metadata = {
            "data_type": "player_profile",
            "player_id": str(player.id),
            "player_name": f"{player.first_name} {player.last_name}",
            "team_id": str(player.team_id) if player.team_id else None,
            "position": player.position,
            "season": season,
            "source": "sportsdata.io",
            "last_verified": datetime.utcnow().isoformat(),
            "confidence_score": 0.95
        }
        
        return self.create_chunks_from_text(profile_text, base_metadata)
    
    def chunk_game_log(
        self,
        player: Player,
        game: Game,
        stats: PlayerGameStats,
        props: Optional[List[PlayerProp]] = None
    ) -> List[DocumentChunk]:
        """
        Create chunks from individual game performance
        
        Args:
            player: Player model instance
            game: Game model instance
            stats: Player's stats for this game
            props: Optional prop lines for this game
            
        Returns:
            List of DocumentChunk objects
        """
        # Build game log text
        game_info = [
            f"Game Log: {player.first_name} {player.last_name}",
            f"Date: {game.game_date.strftime('%Y-%m-%d')}",
            f"Week {game.week} - {game.season.year} Season",
            f"Matchup: {game.away_team.name} @ {game.home_team.name}",
            f"Final Score: {game.away_team.name} {game.away_score} - {game.home_team.name} {game.home_score}",
        ]
        
        if game.stadium:
            game_info.append(f"Stadium: {game.stadium}")
        
        # Add detailed stats based on position
        game_info.append("\nPlayer Performance:")
        game_info.append(self._format_game_stats(stats, player.position, detailed=True))
        
        # Add prop betting context if available
        if props:
            game_info.append("\nProp Betting Lines:")
            for prop in props:
                game_info.append(
                    f"  {prop.prop_type}: {prop.line} "
                    f"(Over: {prop.over_odds}, Under: {prop.under_odds})"
                )
        
        game_text = "\n".join(game_info)
        
        # Base metadata
        base_metadata = {
            "data_type": "game_log",
            "player_id": str(player.id),
            "player_name": f"{player.first_name} {player.last_name}",
            "game_id": str(game.id),
            "season": game.season.year,
            "week": game.week,
            "opponent_id": str(game.home_team_id if player.team_id == game.away_team_id else game.away_team_id),
            "fantasy_points": float(stats.fantasy_points) if stats.fantasy_points else None,
            "source": "sportsdata.io",
            "last_verified": datetime.utcnow().isoformat(),
            "confidence_score": 0.98  # Historical data is highly reliable
        }
        
        return self.create_chunks_from_text(game_text, base_metadata)
    
    def chunk_matchup_analytics(
        self,
        player: Player,
        upcoming_game: Game,
        historical_vs_opponent: List[PlayerGameStats],
        recent_form: List[PlayerGameStats],
        injury_report: Optional[List[Injury]] = None
    ) -> List[DocumentChunk]:
        """
        Create chunks from matchup analysis and projections
        
        Args:
            player: Player model instance
            upcoming_game: Upcoming game
            historical_vs_opponent: Past performances against this opponent
            recent_form: Recent game stats (last 3-5 games)
            injury_report: Current injury status
            
        Returns:
            List of DocumentChunk objects
        """
        # Build matchup analysis
        analysis = [
            f"Matchup Analysis: {player.first_name} {player.last_name}",
            f"Week {upcoming_game.week} - {upcoming_game.season.year}",
            f"Upcoming: {upcoming_game.away_team.name} @ {upcoming_game.home_team.name}",
            f"Game Date: {upcoming_game.game_date.strftime('%Y-%m-%d')}",
        ]
        
        if upcoming_game.spread:
            analysis.append(f"Spread: {upcoming_game.spread}")
        if upcoming_game.over_under:
            analysis.append(f"Over/Under: {upcoming_game.over_under}")
        
        # Injury status
        if injury_report:
            analysis.append("\nInjury Status:")
            for injury in injury_report:
                analysis.append(
                    f"  {injury.injury_status}: {injury.body_part or 'Unspecified'} "
                    f"({injury.practice_status or 'No practice info'})"
                )
        
        # Historical vs opponent
        if historical_vs_opponent:
            analysis.append(f"\nHistorical vs Opponent ({len(historical_vs_opponent)} games):")
            for stat in historical_vs_opponent[:3]:  # Last 3 meetings
                analysis.append(f"  {self._format_game_stats(stat, player.position)}")
            
            # Calculate averages
            avg_stats = self._calculate_average_stats(historical_vs_opponent, player.position)
            analysis.append(f"Average vs Opponent: {avg_stats}")
        
        # Recent form
        if recent_form:
            analysis.append(f"\nRecent Form (Last {len(recent_form)} games):")
            for stat in recent_form:
                analysis.append(f"  {self._format_game_stats(stat, player.position)}")
            
            avg_stats = self._calculate_average_stats(recent_form, player.position)
            analysis.append(f"Recent Average: {avg_stats}")
        
        analysis_text = "\n".join(analysis)
        
        # Base metadata
        base_metadata = {
            "data_type": "matchup_analytics",
            "player_id": str(player.id),
            "player_name": f"{player.first_name} {player.last_name}",
            "game_id": str(upcoming_game.id),
            "season": upcoming_game.season.year,
            "week": upcoming_game.week,
            "opponent_id": str(upcoming_game.home_team_id if player.team_id == upcoming_game.away_team_id else upcoming_game.away_team_id),
            "has_injury": len(injury_report) > 0 if injury_report else False,
            "historical_games": len(historical_vs_opponent),
            "recent_games": len(recent_form),
            "source": "sportsdata.io",
            "last_verified": datetime.utcnow().isoformat(),
            "confidence_score": 0.85  # Projections are less certain
        }
        
        return self.create_chunks_from_text(analysis_text, base_metadata)
    
    def _format_game_stats(
        self,
        stats: PlayerGameStats,
        position: str,
        detailed: bool = False
    ) -> str:
        """Format game stats based on position"""
        if position in ["QB", "Quarterback"]:
            if detailed:
                return (
                    f"Passing: {stats.passing_completions}/{stats.passing_attempts} "
                    f"for {stats.passing_yards} yards, {stats.passing_tds} TDs, {stats.interceptions} INTs. "
                    f"Rushing: {stats.rushing_attempts} att, {stats.rushing_yards} yards, {stats.rushing_tds} TDs. "
                    f"Fantasy: {stats.fantasy_points} pts"
                )
            return f"{stats.passing_yards} pass yds, {stats.passing_tds} TDs, {stats.interceptions} INTs"
        
        elif position in ["RB", "Running Back"]:
            if detailed:
                return (
                    f"Rushing: {stats.rushing_attempts} att, {stats.rushing_yards} yards, {stats.rushing_tds} TDs. "
                    f"Receiving: {stats.receptions}/{stats.receiving_targets} for {stats.receiving_yards} yards, {stats.receiving_tds} TDs. "
                    f"Fantasy: {stats.fantasy_points} pts"
                )
            return f"{stats.rushing_yards} rush yds, {stats.receptions} rec, {stats.receiving_yards} rec yds"
        
        elif position in ["WR", "TE", "Wide Receiver", "Tight End"]:
            if detailed:
                return (
                    f"Receiving: {stats.receptions}/{stats.receiving_targets} for {stats.receiving_yards} yards, {stats.receiving_tds} TDs. "
                    f"Rushing: {stats.rushing_attempts} att, {stats.rushing_yards} yards. "
                    f"Fantasy: {stats.fantasy_points} pts"
                )
            return f"{stats.receptions}/{stats.receiving_targets} rec, {stats.receiving_yards} yards, {stats.receiving_tds} TDs"
        
        else:
            return f"Fantasy Points: {stats.fantasy_points}"
    
    def _calculate_average_stats(
        self,
        stats_list: List[PlayerGameStats],
        position: str
    ) -> str:
        """Calculate average stats across multiple games"""
        if not stats_list:
            return "No data"
        
        n = len(stats_list)
        
        if position in ["QB", "Quarterback"]:
            avg_pass_yds = sum(s.passing_yards or 0 for s in stats_list) / n
            avg_pass_tds = sum(s.passing_tds or 0 for s in stats_list) / n
            avg_ints = sum(s.interceptions or 0 for s in stats_list) / n
            return f"{avg_pass_yds:.1f} pass yds, {avg_pass_tds:.1f} TDs, {avg_ints:.1f} INTs"
        
        elif position in ["RB", "Running Back"]:
            avg_rush_yds = sum(s.rushing_yards or 0 for s in stats_list) / n
            avg_rec_yds = sum(s.receiving_yards or 0 for s in stats_list) / n
            avg_tds = sum((s.rushing_tds or 0) + (s.receiving_tds or 0) for s in stats_list) / n
            return f"{avg_rush_yds:.1f} rush yds, {avg_rec_yds:.1f} rec yds, {avg_tds:.1f} TDs"
        
        elif position in ["WR", "TE", "Wide Receiver", "Tight End"]:
            avg_rec = sum(s.receptions or 0 for s in stats_list) / n
            avg_rec_yds = sum(s.receiving_yards or 0 for s in stats_list) / n
            avg_rec_tds = sum(s.receiving_tds or 0 for s in stats_list) / n
            return f"{avg_rec:.1f} rec, {avg_rec_yds:.1f} yards, {avg_rec_tds:.1f} TDs"
        
        else:
            avg_fantasy = sum(s.fantasy_points or 0 for s in stats_list) / n
            return f"{avg_fantasy:.1f} fantasy pts"
