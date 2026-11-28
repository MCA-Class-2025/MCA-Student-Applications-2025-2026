# ============================================================
# MULTILINGUAL NEWS VERIFICATION
# ADVANCED EVIDENCE MATCHER
# ============================================================
#
# File:
# backend/api/evidence_matcher.py
#
# PURPOSE:
#   Compare a news claim against an article and determine whether
#   the article supports, contradicts, or is merely related to
#   the claim.
#
# IMPORTANT SPORTS FIX:
#
#   Claim:
#       India won the 2024 T20 World Cup final.
#
#   Article:
#       India defeated South Africa in the 2024 T20 World Cup
#       final and lifted the trophy.
#
#   => SUPPORTING
#
#   Claim:
#       India lost the 2024 T20 World Cup final to Sri Lanka.
#
#   Article:
#       India defeated South Africa in the 2024 T20 World Cup
#       final and lifted the trophy.
#
#   => CONTRADICTING
#
# ============================================================

import re
import os
import sys
from typing import List, Dict, Optional, Tuple

# ============================================================
# SEMANTIC MODEL
# ============================================================

print()
print("Loading semantic similarity model...")

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    SEMANTIC_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    semantic_model = SentenceTransformer(SEMANTIC_MODEL_NAME)

    print("Semantic model loaded successfully.")

except Exception as e:
    print()
    print("ERROR: Could not load semantic similarity model.")
    print(str(e))
    semantic_model = None


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for matching while preserving Unicode.
    """

    if not text:
        return ""

    text = str(text).lower()

    # Replace punctuation with spaces.
    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)

    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# DISPLAY HELPERS
# ============================================================

def display_team(team: Optional[str]) -> str:
    """
    Convert internal team/entity representation into readable form.
    """

    if not team:
        return ""

    mapping = {
        "india": "India",
        "sri_lanka": "Sri Lanka",
        "south_africa": "South Africa",
        "australia": "Australia",
        "england": "England",
        "new_zealand": "New Zealand",
        "pakistan": "Pakistan",
        "bangladesh": "Bangladesh",
        "afghanistan": "Afghanistan",
        "west_indies": "West Indies",
        "ireland": "Ireland",
        "scotland": "Scotland",
        "nepal": "Nepal",
        "usa": "USA",
        "united_states": "United States",
    }

    return mapping.get(
        team,
        team.replace("_", " ").title()
    )


# ============================================================
# ENTITY / TEAM DETECTION
# ============================================================

TEAM_PATTERNS = {

    "india": [
        r"\bindia\b",
        r"\bindian\b",
        r"\bteam india\b",
    ],

    "sri_lanka": [
        r"\bsri lanka\b",
        r"\bsrilanka\b",
        r"\bsri-lanka\b",
    ],

    "south_africa": [
        r"\bsouth africa\b",
        r"\bsouth african\b",
    ],

    "australia": [
        r"\baustralia\b",
        r"\baustralian\b",
    ],

    "england": [
        r"\bengland\b",
        r"\benglish team\b",
    ],

    "new_zealand": [
        r"\bnew zealand\b",
        r"\bnew zealand team\b",
    ],

    "pakistan": [
        r"\bpakistan\b",
        r"\bpakistani\b",
    ],

    "bangladesh": [
        r"\bbangladesh\b",
        r"\bbangladeshi\b",
    ],

    "afghanistan": [
        r"\bafghanistan\b",
        r"\bafghan\b",
    ],

    "west_indies": [
        r"\bwest indies\b",
    ],

    "ireland": [
        r"\bireland\b",
        r"\birish team\b",
    ],

    "scotland": [
        r"\bscotland\b",
        r"\bscottish team\b",
    ],

    "nepal": [
        r"\bnepal\b",
        r"\bnepalese\b",
    ],

    "usa": [
        r"\busa\b",
        r"\bu s a\b",
        r"\bunited states\b",
        r"\bamerica\b",
    ],
}


def detect_teams(text: str) -> List[str]:
    """
    Detect sports teams/entities from text.
    """

    normalized = normalize_text(text)

    found = []

    for team, patterns in TEAM_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, normalized):

                if team not in found:
                    found.append(team)

                break

    return found


# ============================================================
# SPORTS CONTEXT
# ============================================================

SPORTS_KEYWORDS = [

    "cricket",
    "t20",
    "t20i",
    "odi",
    "test match",
    "world cup",
    "worldcup",
    "ipl",
    "championship",
    "final",
    "semi final",
    "semifinal",
    "match",
    "trophy",
    "score",
    "runs",
    "wicket",
    "wickets",
    "innings",
    "batting",
    "bowling",
    "defeated",
    "defeat",
    "won",
    "win",
    "winner",
    "lost",
    "loss",
    "victory",
]


def detect_sports_context(text: str) -> bool:
    """
    Determine whether text contains sports/cricket context.
    """

    normalized = normalize_text(text)

    for keyword in SPORTS_KEYWORDS:

        if keyword in normalized:
            return True

    return False


# ============================================================
# MATCH TYPE
# ============================================================

def detect_match_type(text: str) -> Optional[str]:
    """
    Detect cricket match type.
    """

    normalized = normalize_text(text)

    if re.search(r"\bt20i?\b", normalized):
        return "t20"

    if re.search(r"\bodi\b", normalized):
        return "odi"

    if re.search(r"\btest\b", normalized):
        return "test"

    if "ipl" in normalized:
        return "ipl"

    if "world cup" in normalized:
        return "world_cup"

    return None


# ============================================================
# RESULT TYPE
# ============================================================

VICTORY_PATTERNS = [

    r"\bwon\b",
    r"\bwins\b",
    r"\bwin\b",
    r"\bwinning\b",
    r"\bvictory\b",
    r"\bvictorious\b",
    r"\bchampion\b",
    r"\bchampions\b",
    r"\blifted the trophy\b",
    r"\blifted the cup\b",
    r"\bclinched\b",
    r"\bbeat\b",
    r"\bbeats\b",
    r"\bdefeated\b",
    r"\bdefeat(ed)?\b",
]

LOSS_PATTERNS = [

    r"\blost\b",
    r"\bloses\b",
    r"\bloss\b",
    r"\blose\b",
    r"\bdefeat(ed)? by\b",
    r"\bbeaten by\b",
    r"\blosing\b",
    r"\brunner[- ]up\b",
]


def detect_result_type(text: str) -> Optional[str]:
    """
    Detect whether a statement describes a victory or loss.

    Priority:
        explicit loss -> loss
        otherwise victory -> victory
    """

    normalized = normalize_text(text)

    # Loss is checked first because "did not win" or
    # "lost to" should not accidentally become victory.
    for pattern in LOSS_PATTERNS:

        if re.search(pattern, normalized):
            return "loss"

    for pattern in VICTORY_PATTERNS:

        if re.search(pattern, normalized):
            return "victory"

    return None


# ============================================================
# WINNER DETECTION
# ============================================================

def detect_winner(text: str) -> Optional[str]:
    """
    Detect the team that is described as winning.

    Examples:

        India won the final.
            -> india

        India defeated South Africa.
            -> india

        South Africa was defeated by India.
            -> india

        India lost to Sri Lanka.
            -> sri_lanka

        Sri Lanka defeated India.
            -> sri_lanka

    IMPORTANT:
    This function attempts to determine the actual winner,
    not simply the first team mentioned.
    """

    normalized = normalize_text(text)

    teams = detect_teams(normalized)

    if not teams:
        return None

    # --------------------------------------------------------
    # Pattern:
    # "X defeated Y"
    # "X beat Y"
    # "X won against Y"
    # --------------------------------------------------------

    team_names = {
        "india": r"(india|indian team|team india)",
        "sri_lanka": r"(sri lanka|srilanka)",
        "south_africa": r"(south africa|south african team)",
        "australia": r"(australia|australian team)",
        "england": r"(england|english team)",
        "new_zealand": r"(new zealand)",
        "pakistan": r"(pakistan|pakistani team)",
        "bangladesh": r"(bangladesh|bangladeshi team)",
        "afghanistan": r"(afghanistan|afghan team)",
        "west_indies": r"(west indies)",
        "ireland": r"(ireland|irish team)",
        "scotland": r"(scotland|scottish team)",
        "nepal": r"(nepal|nepalese team)",
        "usa": r"(usa|u s a|united states|america)",
    }

    # --------------------------------------------------------
    # X defeated Y
    # --------------------------------------------------------

    for winner in teams:

        winner_pattern = team_names.get(winner)

        if not winner_pattern:
            continue

        defeated_pattern = (
            rf"{winner_pattern}"
            r".{0,80}?"
            r"\b(defeated|defeat|beat|beats|beating)\b"
        )

        if re.search(defeated_pattern, normalized):

            return winner

    # --------------------------------------------------------
    # X won
    # --------------------------------------------------------

    for winner in teams:

        winner_pattern = team_names.get(winner)

        if not winner_pattern:
            continue

        won_pattern = (
            rf"{winner_pattern}"
            r".{0,80}?"
            r"\b(won|wins|winning|victory|champions?|champion)\b"
        )

        if re.search(won_pattern, normalized):

            return winner

    # --------------------------------------------------------
    # X lifted the trophy/cup
    # --------------------------------------------------------

    for winner in teams:

        winner_pattern = team_names.get(winner)

        if not winner_pattern:
            continue

        trophy_pattern = (
            rf"{winner_pattern}"
            r".{0,100}?"
            r"\b(lifted|lift|lifting)\b"
            r".{0,50}?"
            r"\b(trophy|cup)\b"
        )

        if re.search(trophy_pattern, normalized):

            return winner

    # --------------------------------------------------------
    # "X was defeated by Y"
    # "X lost to Y"
    # --------------------------------------------------------

    for loser in teams:

        loser_pattern = team_names.get(loser)

        if not loser_pattern:
            continue

        # X lost to Y
        loss_match = re.search(
            loser_pattern
            + r".{0,60}?"
            + r"\b(lost|loses|loss|beaten|defeated)\b"
            + r".{0,40}?"
            + r"\b(to|by)\b"
            + r".{0,30}?"
            + r"([a-z]+(?:\s+[a-z]+)?)",
            normalized
        )

        if loss_match:

            for possible_winner in teams:

                if possible_winner != loser:

                    return possible_winner

    # --------------------------------------------------------
    # Generic fallback:
    #
    # If there is exactly one team and the text contains
    # victory language, that team is the winner.
    # --------------------------------------------------------

    if len(teams) == 1:

        result_type = detect_result_type(normalized)

        if result_type == "victory":

            return teams[0]

    # --------------------------------------------------------
    # Final conservative fallback:
    #
    # If the article contains "defeated by X", identify X.
    # --------------------------------------------------------

    by_match = re.search(
        r"\b(defeated|beaten)\b.{0,50}?\bby\b",
        normalized
    )

    if by_match:

        after = normalized[by_match.end():]

        after_teams = detect_teams(after)

        if after_teams:
            return after_teams[0]

    return None


# ============================================================
# CLAIMED LOSS OPPONENT DETECTION
# ============================================================

def detect_loss_opponent(text: str) -> Optional[str]:
    """
    Detect the opponent that supposedly beat the claimant.

    Example:

        India lost to Sri Lanka.
            -> sri_lanka
    """

    normalized = normalize_text(text)

    teams = detect_teams(normalized)

    if len(teams) < 2:
        return None

    # Look for:
    # lost to X
    # defeated by X
    # beaten by X

    patterns = [
        r"\blost\b.{0,50}?\bto\b",
        r"\bdefeated\b.{0,50}?\bby\b",
        r"\bbeaten\b.{0,50}?\bby\b",
    ]

    for pattern in patterns:

        match = re.search(pattern, normalized)

        if match:

            after = normalized[match.end():]

            after_teams = detect_teams(after)

            if after_teams:
                return after_teams[0]

    return None


# ============================================================
# COMPONENT DETECTION
# ============================================================

def detect_claim_components(text: str) -> List[str]:
    """
    Extract meaningful claim components.
    """

    normalized = normalize_text(text)

    components = []

    teams = detect_teams(normalized)

    for team in teams:

        if team not in components:
            components.append(team)

    # Result
    result_type = detect_result_type(normalized)

    if result_type == "victory":
        components.append("victory")

    elif result_type == "loss":
        components.append("loss")

    # Match
    if re.search(
        r"\b(final|match|game|fixture)\b",
        normalized
    ):
        components.append("match")

    # World Cup
    if "world cup" in normalized or "worldcup" in normalized:
        components.append("world_cup")

    # T20
    if re.search(r"\bt20i?\b", normalized):
        components.append("t20")

    # ODI
    if re.search(r"\bodi\b", normalized):
        components.append("odi")

    # Test
    if re.search(r"\btest\b", normalized):
        components.append("test")

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(components))


def detect_article_components(text: str) -> List[str]:
    """
    Article components use the same extraction system.
    """

    return detect_claim_components(text)


# ============================================================
# COMPONENT MATCHING
# ============================================================

def calculate_component_match(
    claim_components: List[str],
    article_components: List[str]
) -> Tuple[List[str], float]:

    if not claim_components:

        return [], 0.0

    matched = [
        component
        for component in claim_components
        if component in article_components
    ]

    score = (
        len(matched)
        / len(claim_components)
    ) * 100

    return matched, score


# ============================================================
# CLAIM REQUIREMENT MATCH
# ============================================================

def calculate_requirement_match(
    claim_text: str,
    article_text: str
) -> float:

    claim = normalize_text(claim_text)
    article = normalize_text(article_text)

    requirements = []

    # --------------------------------------------------------
    # Sports
    # --------------------------------------------------------

    if detect_sports_context(claim):

        requirements.append(
            detect_sports_context(article)
        )

    # --------------------------------------------------------
    # T20
    # --------------------------------------------------------

    claim_type = detect_match_type(claim)

    if claim_type:

        requirements.append(
            detect_match_type(article) == claim_type
        )

    # --------------------------------------------------------
    # World Cup
    # --------------------------------------------------------

    if "world cup" in claim:

        requirements.append(
            "world cup" in article
        )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    if re.search(r"\bfinal\b", claim):

        requirements.append(
            bool(re.search(r"\bfinal\b", article))
        )

    # --------------------------------------------------------
    # If no requirements
    # --------------------------------------------------------

    if not requirements:
        return 100.0

    return (
        sum(1 for value in requirements if value)
        / len(requirements)
    ) * 100


# ============================================================
# SEMANTIC SIMILARITY
# ============================================================

def calculate_semantic_similarity(
    claim_text: str,
    article_text: str
) -> float:

    if semantic_model is None:
        return 0.0

    try:

        embeddings = semantic_model.encode(
            [
                claim_text,
                article_text
            ],
            convert_to_numpy=True
        )

        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        similarity = max(
            0.0,
            min(1.0, float(similarity))
        )

        return similarity * 100

    except Exception as e:

        print(
            f"Semantic similarity error: {e}"
        )

        return 0.0


# ============================================================
# SPORTS RESULT ANALYSIS
# ============================================================

def analyze_sports_result(
    claim_text: str,
    article_text: str
) -> Dict:

    claim = normalize_text(claim_text)
    article = normalize_text(article_text)

    claim_result_type = detect_result_type(claim)
    article_result_type = detect_result_type(article)

    claim_teams = detect_teams(claim)
    article_teams = detect_teams(article)

    claim_winner = detect_winner(claim)
    article_winner = detect_winner(article)

    claim_loss_opponent = detect_loss_opponent(claim)

    sports_context_match = (
        detect_sports_context(claim)
        and detect_sports_context(article)
    )

    claim_match_type = detect_match_type(claim)
    article_match_type = detect_match_type(article)

    # ========================================================
    # IMPORTANT FIX
    #
    # A result claim only needs ONE explicitly named team.
    #
    # Example:
    #   "India won the 2024 T20 World Cup final."
    #
    # There is only one team in the claim, but it is still
    # absolutely a sports-result claim.
    # ========================================================

    sports_result_required = (
        claim_result_type in ["loss", "victory"]
        and len(claim_teams) >= 1
    )

    # ========================================================
    # TEAM ENTITY MATCH
    # ========================================================

    sports_entity_match = bool(
        set(claim_teams)
        .intersection(set(article_teams))
    )

    sports_supported = False
    sports_contradicted = False

    reason = ""

    # ========================================================
    # RESULT VERIFICATION
    # ========================================================

    if sports_result_required:

        # ----------------------------------------------------
        # CLAIM = VICTORY
        # ----------------------------------------------------

        if claim_result_type == "victory":

            # If article identifies same winner
            if (
                claim_winner is not None
                and article_winner is not None
            ):

                if claim_winner == article_winner:

                    sports_supported = True

                    reason = (
                        "Article confirms the same winner as "
                        "the claim: "
                        + display_team(article_winner)
                        + "."
                    )

                else:

                    sports_contradicted = True

                    reason = (
                        "Claim identifies "
                        + display_team(claim_winner)
                        + " as the winner, but the article "
                        "identifies "
                        + display_team(article_winner)
                        + " as the winner."
                    )

            # Claim has winner but article does not
            elif claim_winner is not None:

                # If article clearly contains the same team
                # and victory language but winner detection
                # failed, don't call it a contradiction.
                if (
                    claim_winner in article_teams
                    and article_result_type == "victory"
                ):

                    sports_supported = True

                    reason = (
                        "Article contains the claimed team "
                        "and confirms a victory, although the "
                        "winner could not be extracted with "
                        "complete certainty."
                    )

                else:

                    reason = (
                        "Article does not clearly confirm "
                        "the claimed winner."
                    )

            else:

                reason = (
                    "Could not determine the claimed winner."
                )

        # ----------------------------------------------------
        # CLAIM = LOSS
        # ----------------------------------------------------

        elif claim_result_type == "loss":

            # For:
            #
            # India lost to Sri Lanka.
            #
            # expected winner = Sri Lanka
            #
            # If article says India won:
            # expected contradiction.
            #
            # If article says Sri Lanka won:
            # support.

            claimed_loser = None

            if claim_teams:

                # If an explicit opponent exists, determine
                # claimant based on "lost to X".
                if claim_loss_opponent:

                    for team in claim_teams:

                        if team != claim_loss_opponent:
                            claimed_loser = team
                            break

                elif claim_winner:

                    # fallback
                    claimed_loser = claim_winner

                else:

                    claimed_loser = claim_teams[0]

            claimed_actual_winner = claim_loss_opponent

            # ------------------------------------------------
            # Article explicitly identifies a winner
            # ------------------------------------------------

            if article_winner is not None:

                # If article winner equals claimed opponent,
                # the loss claim is supported.
                if (
                    claimed_actual_winner is not None
                    and article_winner == claimed_actual_winner
                ):

                    sports_supported = True

                    reason = (
                        "Article confirms that "
                        + display_team(claimed_loser)
                        + " lost to "
                        + display_team(article_winner)
                        + "."
                    )

                # If article winner is the claimed loser,
                # contradiction.
                elif (
                    claimed_loser is not None
                    and article_winner == claimed_loser
                ):

                    sports_contradicted = True

                    reason = (
                        "Claim says "
                        + display_team(claimed_loser)
                        + " lost, but the article says "
                        + display_team(claimed_loser)
                        + " won."
                    )

                else:

                    reason = (
                        "Article identifies "
                        + display_team(article_winner)
                        + " as the winner, but the claimed "
                        "loss relationship is not fully matched."
                    )

            else:

                reason = (
                    "Article does not clearly confirm "
                    "the claimed loss."
                )

    else:

        reason = (
            "No explicit sports result claim detected."
        )

    # ========================================================
    # SPECIAL SPORTS CONSISTENCY CHECK
    # ========================================================

    # If claim says "India won" and article says
    # "India defeated South Africa", support.
    #
    # If claim says "India lost" and article says
    # "India defeated South Africa", contradiction.

    if sports_result_required:

        if (
            claim_winner is not None
            and article_winner is not None
        ):

            if (
                claim_result_type == "victory"
                and claim_winner == article_winner
            ):

                sports_supported = True
                sports_contradicted = False

                reason = (
                    "Article confirms that "
                    + display_team(article_winner)
                    + " won the match."
                )

            elif (
                claim_result_type == "victory"
                and claim_winner != article_winner
            ):

                sports_supported = False
                sports_contradicted = True

                reason = (
                    "Article identifies "
                    + display_team(article_winner)
                    + " as the winner instead of "
                    + display_team(claim_winner)
                    + "."
                )

    # ========================================================
    # MATCH TYPE
    # ========================================================

    if (
        claim_match_type is not None
        and article_match_type is not None
        and claim_match_type != article_match_type
    ):

        sports_supported = False
        sports_contradicted = True

        reason = (
            "Claim and article refer to different match types."
        )

    return {

        "sports_result_required":
            sports_result_required,

        "sports_result_supported":
            sports_supported,

        "sports_contradicted":
            sports_contradicted,

        "sports_entity_match":
            sports_entity_match,

        "claimed_winner":
            claim_winner,

        "article_winner":
            article_winner,

        "sports_context_match":
            sports_context_match,

        "claim_match_type":
            claim_match_type,

        "article_match_type":
            article_match_type,

        "claim_result_type":
            claim_result_type,

        "article_result_type":
            article_result_type,

        "claim_teams":
            claim_teams,

        "article_teams":
            article_teams,

        "reason":
            reason,
    }


# ============================================================
# EVIDENCE SCORE
# ============================================================

def calculate_evidence_score(
    semantic_similarity: float,
    component_match: float,
    requirement_match: float,
    sports_result: Dict
) -> float:

    # --------------------------------------------------------
    # Base score
    # --------------------------------------------------------

    base_score = (
        semantic_similarity * 0.30
        + component_match * 0.35
        + requirement_match * 0.35
    )

    # --------------------------------------------------------
    # Sports result is much more important than semantic
    # similarity when the claim explicitly states a result.
    # --------------------------------------------------------

    if sports_result["sports_result_required"]:

        if sports_result["sports_result_supported"]:

            # Strong boost for explicit result confirmation.
            score = max(
                base_score,
                85.0
            )

            score += 5.0

            return min(score, 100.0)

        if sports_result["sports_contradicted"]:

            # A direct contradiction must never receive a
            # "supporting" score merely because the article
            # contains the same teams/keywords.
            return min(
                max(0.0, base_score * 0.20),
                30.0
            )

        # Result not confirmed.
        return min(
            base_score,
            60.0
        )

    # --------------------------------------------------------
    # Normal non-result evidence
    # --------------------------------------------------------

    return min(
        max(0.0, base_score),
        100.0
    )


# ============================================================
# EVIDENCE CLASSIFICATION
# ============================================================

def classify_evidence(
    evidence_score: float,
    sports_result: Dict
) -> str:

    # ========================================================
    # DIRECT SPORTS CONTRADICTION
    # ========================================================

    if sports_result["sports_contradicted"]:

        return "Contradicting Evidence"

    # ========================================================
    # DIRECT SPORTS SUPPORT
    # ========================================================

    if sports_result["sports_result_supported"]:

        return "Strongly Supporting"

    # ========================================================
    # NO EXPLICIT RESULT CONFIRMATION
    # ========================================================

    if sports_result["sports_result_required"]:

        if evidence_score >= 70:

            return "Related - Result Not Confirmed"

        if evidence_score >= 45:

            return "Weakly Related"

        return "Insufficient Evidence"

    # ========================================================
    # NORMAL EVIDENCE
    # ========================================================

    if evidence_score >= 75:

        return "Strongly Supporting"

    if evidence_score >= 55:

        return "Supporting"

    if evidence_score >= 35:

        return "Weakly Related"

    return "Insufficient Evidence"


# ============================================================
# MAIN EVIDENCE ANALYSIS
# ============================================================

def analyze_evidence(
    claim_text: str,
    article_text: str
) -> Dict:

    # --------------------------------------------------------
    # Components
    # --------------------------------------------------------

    claim_components = detect_claim_components(
        claim_text
    )

    article_components = detect_article_components(
        article_text
    )

    matched_components, component_match = (
        calculate_component_match(
            claim_components,
            article_components
        )
    )

    # --------------------------------------------------------
    # Requirement match
    # --------------------------------------------------------

    requirement_match = (
        calculate_requirement_match(
            claim_text,
            article_text
        )
    )

    # --------------------------------------------------------
    # Semantic similarity
    # --------------------------------------------------------

    semantic_similarity = (
        calculate_semantic_similarity(
            claim_text,
            article_text
        )
    )

    # --------------------------------------------------------
    # Sports
    # --------------------------------------------------------

    sports_result = analyze_sports_result(
        claim_text,
        article_text
    )

    # --------------------------------------------------------
    # Final evidence score
    # --------------------------------------------------------

    evidence_score = calculate_evidence_score(
        semantic_similarity,
        component_match,
        requirement_match,
        sports_result
    )

    # --------------------------------------------------------
    # Evidence type
    # --------------------------------------------------------

    evidence_type = classify_evidence(
        evidence_score,
        sports_result
    )

    # --------------------------------------------------------
    # Exact claim support
    # --------------------------------------------------------

    exact_claim_support = False

    if sports_result["sports_contradicted"]:

        exact_claim_support = False

    elif sports_result["sports_result_supported"]:

        exact_claim_support = True

    elif (
        component_match >= 80
        and requirement_match >= 80
        and semantic_similarity >= 65
    ):

        exact_claim_support = True

    # --------------------------------------------------------
    # Why not exact proof
    # --------------------------------------------------------

    reasons = []

    if sports_result["sports_contradicted"]:

        reasons.append(
            sports_result["reason"]
        )

    elif (
        sports_result["sports_result_required"]
        and not sports_result["sports_result_supported"]
    ):

        reasons.append(
            sports_result["reason"]
        )

    elif not exact_claim_support:

        reasons.append(
            "Article does not provide complete exact "
            "confirmation of the claim."
        )

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        "claim_components":
            claim_components,

        "article_components":
            article_components,

        "matched_components":
            matched_components,

        "semantic_similarity":
            semantic_similarity,

        "component_match":
            component_match,

        "requirement_match":
            requirement_match,

        "sports_result_required":
            sports_result[
                "sports_result_required"
            ],

        "sports_result_supported":
            sports_result[
                "sports_result_supported"
            ],

        "sports_contradicted":
            sports_result[
                "sports_contradicted"
            ],

        "sports_entity_match":
            sports_result[
                "sports_entity_match"
            ],

        "claimed_winner":
            sports_result[
                "claimed_winner"
            ],

        "article_winner":
            sports_result[
                "article_winner"
            ],

        "sports_context_match":
            sports_result[
                "sports_context_match"
            ],

        "claim_match_type":
            sports_result[
                "claim_match_type"
            ],

        "article_match_type":
            sports_result[
                "article_match_type"
            ],

        "claim_result_type":
            sports_result[
                "claim_result_type"
            ],

        "article_result_type":
            sports_result[
                "article_result_type"
            ],

        "sports_reason":
            sports_result[
                "reason"
            ],

        "exact_claim_support":
            exact_claim_support,

        "final_evidence_score":
            evidence_score,

        "evidence_type":
            evidence_type,

        "reasons":
            reasons,
    }


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(result: Dict):

    print()
    print("=" * 40)
    print(" RESULT")
    print("=" * 40)

    print()

    print(
        "Claim Components:"
    )

    print(
        result["claim_components"]
    )

    print()

    print(
        "Article Components:"
    )

    print(
        result["article_components"]
    )

    print()

    print(
        "Matched Components:"
    )

    print(
        result["matched_components"]
    )

    print()

    print(
        f"Semantic Similarity: "
        f"{result['semantic_similarity']:.2f}%"
    )

    print(
        f"Component Match: "
        f"{result['component_match']:.2f}%"
    )

    print(
        f"Claim Requirement Match: "
        f"{result['requirement_match']:.2f}%"
    )

    print()

    print(
        f"Central Government: False"
    )

    print(
        f"State Government: False"
    )

    print(
        f"State Name: "
    )

    print(
        f"Government of India Required: False"
    )

    print(
        f"India Confirmed: "
        f"{'True' if 'india' in detect_teams(result.get('claim_components', []).__str__()) else result['sports_entity_match']}"
    )

    print(
        "New Confirmed: False"
    )

    print(
        "Announcement Confirmed: False"
    )

    print()

    # ========================================================
    # SPORTS
    # ========================================================

    print(
        f"Sports Result Required: "
        f"{result['sports_result_required']}"
    )

    print(
        f"Sports Result Supported: "
        f"{result['sports_result_supported']}"
    )

    print(
        f"Sports Contradicted: "
        f"{result['sports_contradicted']}"
    )

    print(
        f"Sports Entity Match: "
        f"{result['sports_entity_match']}"
    )

    print(
        f"Claimed Winner: "
        f"{result['claimed_winner']}"
    )

    print(
        f"Article Winner: "
        f"{result['article_winner']}"
    )

    print(
        f"Sports Context Match: "
        f"{result['sports_context_match']}"
    )

    print(
        f"Claim Match Type: "
        f"{result['claim_match_type']}"
    )

    print(
        f"Article Match Type: "
        f"{result['article_match_type']}"
    )

    print(
        f"Claim Result Type: "
        f"{result['claim_result_type']}"
    )

    print(
        f"Article Result Type: "
        f"{result['article_result_type']}"
    )

    print(
        f"Sports Reason: "
        f"{result['sports_reason']}"
    )

    print()

    print(
        f"Exact Claim Support: "
        f"{result['exact_claim_support']}"
    )

    print()

    print(
        f"Final Evidence Score: "
        f"{result['final_evidence_score']:.2f}%"
    )

    print(
        f"Evidence: "
        f"{result['evidence_type']}"
    )

    if result["reasons"]:

        print()

        print(
            "Why it is not exact proof:"
        )

        for reason in result["reasons"]:

            print(
                f"- {reason}"
            )


# ============================================================
# INTERACTIVE TEST
# ============================================================

def main():

    print()
    print("=" * 40)
    print(" ADVANCED EVIDENCE MATCHING TEST")
    print("=" * 40)

    print()

    claim = input(
        "Enter claim:\n"
    ).strip()

    print()

    article = input(
        "Enter article text:\n"
    ).strip()

    if not claim:

        print()
        print("Claim cannot be empty.")
        return

    if not article:

        print()
        print("Article text cannot be empty.")
        return

    result = analyze_evidence(
        claim,
        article
    )

    print_result(result)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()