def check_missing_chapters(found_numbers):
    """Returns a list of missing chapter numbers based on the list of found numbers."""
    if not found_numbers:
        return []
        
    min_num = min(found_numbers)
    max_num = max(found_numbers)
    
    # Using a set internally for faster lookups when checking missing gaps
    found_set = set(found_numbers)
    
    missing_numbers = []
    for i in range(min_num, max_num + 1):
        if i not in found_set and i != 0:
            missing_numbers.append(i)
            
    return missing_numbers


def check_inconsistencies(ordered_numbers):
    """
    Detects numbers that break the sequential order.
    Example: [10, 11, 32, 12, 13] -> Flags 32 as a spike.
    """
    anomalies = []
    
    # We need at least 2 items to compare sequences
    if not ordered_numbers or len(ordered_numbers) < 2:
        return anomalies
        
    # Ensure ordered_numbers is a list (though it should be passed as one)
    ordered_numbers = list(ordered_numbers)
        
    for i in range(1, len(ordered_numbers)):
        prev = ordered_numbers[i-1]
        curr = ordered_numbers[i]
        
        if curr == prev:
            anomalies.append(f"Duplicate chapter detected: **{curr}**")
        elif curr != prev + 1:
            # Let's peek at the NEXT number to classify the anomaly
            if i + 1 < len(ordered_numbers):
                nxt = ordered_numbers[i+1]
                if nxt == prev + 1:
                    anomalies.append(f"Spike detected: **{curr}** (Inserted between {prev} and {nxt})")
                elif nxt == prev + 2:
                    anomalies.append(f"Replacement spike: **{curr}** (Expected {prev + 1}, followed by {nxt})")
                else:
                    anomalies.append(f"Jump detected: From **{prev}** straight to **{curr}**")
            else:
                anomalies.append(f"Ending jump detected: From **{prev}** to **{curr}**")
                
    return anomalies
