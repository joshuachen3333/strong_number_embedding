# Change Proposal: Add RefTerm-Based Refinement

## Summary
Replace dictionary-dependent refinement with a direct RefTerm-based semantic matching approach that uses the reference terms from UNV+SN as the authoritative semantic baseline.

## Problem Statement
Current refinement system has critical limitations:
- Dictionary quality is poor (e.g., H0430 shows "(複數)" instead of semantic meaning)
- Dictionary-based matching achieves only ~50% refinement success rate
- External dictionaries introduce unnecessary complexity and errors
- RefTerms from UNV+SN are already the most authoritative translation reference

## Proposed Solution
Implement RefTerm-based refinement that:
1. Uses RefTerm from UNV+SN as the ground truth
2. Directly matches RefTerm semantics against target text segments
3. Eliminates dependency on external dictionaries
4. Builds semantic clusters from multiple Bible versions
5. Leverages self-learning from UNV+SN corpus

## Key Changes
1. **Remove dictionary dependency**: RefTerm becomes the primary semantic baseline
2. **Direct semantic matching**: Match RefTerm embeddings directly with target segments
3. **Multi-version clustering**: Build semantic clusters from parallel translations
4. **Self-learning capability**: Extract Strong's-to-Chinese mappings from UNV+SN itself

## Benefits
- Improved accuracy: Expected 75-85% match rate (vs current 57%)
- Simpler architecture: Remove unreliable dictionary layer
- Better semantic understanding: RefTerms are actual biblical usage
- Self-improving: Can learn from more parallel texts

## Implementation Approach
1. Create RefTermSemanticEngine class
2. Build RefTerm extraction and embedding pipeline
3. Implement multi-version semantic clustering
4. Add self-learning from UNV+SN corpus
5. Replace dictionary-based refinement with RefTerm matching

## Risks & Mitigations
- **Risk**: RefTerms might have multiple valid translations
- **Mitigation**: Use semantic clustering to capture variants

## Success Criteria
- Refinement success rate > 75%
- Correctly match common terms like 神/上帝, 耶和華/永恆主
- No dependency on external dictionaries
- Pass all existing tests plus new RefTerm-specific tests