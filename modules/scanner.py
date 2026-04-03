def check_missing_chapters(found_numbers):
    """Returns a list of missing chapter numbers based on the set of found numbers."""
    if not found_numbers:
        return []
        
    min_num = min(found_numbers)
    max_num = max(found_numbers)
    
    missing_numbers = []
    for i in range(min_num, max_num + 1):
        if i not in found_numbers and i != 0:
            missing_numbers.append(i)
            
    return missing_numbers
