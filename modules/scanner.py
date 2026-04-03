def check_missing_chapters(found_numbers):
    """
    Returns a dictionary containing missing chapters and anomalous/leftover numbers.
    Expects 'found_numbers' to be an ordered list.
    """
    if not found_numbers:
        return {"missing": [], "anomalies": []}
        
    anomalies = []
    
    # 1. Detect anomalies (sudden spikes that drop back down)
    if len(found_numbers) > 2:
        for i in range(1, len(found_numbers) - 1):
            prev_val = found_numbers[i-1]
            curr_val = found_numbers[i]
            next_val = found_numbers[i+1]
            
            # Anomaly condition: The number jumps up significantly from the previous chapter, 
            # AND the very next chapter drops back down to the normal sequence.
            if (curr_val - prev_val > 5) and (curr_val - next_val > 5):
                anomalies.append(curr_val)
                
    # Check the very first and very last items for isolated, massive jumps
    if len(found_numbers) >= 2:
        if found_numbers[0] - found_numbers[1] > 5:
            anomalies.append(found_numbers[0])
        if found_numbers[-1] - found_numbers[-2] > 5:
            anomalies.append(found_numbers[-1])

    # Remove duplicates from anomalies
    anomalies = list(set(anomalies))

    # 2. Detect missing numbers (ignoring anomalies so max_num isn't distorted)
    valid_numbers = [n for n in found_numbers if n not in anomalies and n != 0]
    missing_numbers = []
    
    if valid_numbers:
        min_num = min(valid_numbers)
        max_num = max(valid_numbers)
        
        # Using a set for O(1) lookups
        valid_set = set(valid_numbers)
        
        for i in range(min_num, max_num + 1):
            if i not in valid_set:
                missing_numbers.append(i)
                
    return {
        "missing": missing_numbers,
        "anomalies": anomalies
    }
