def find_free_key(dictionary, start = 1):
    """Find the first int key available in the dictionary, starting from start.
    """

    #Get a sorted list of the int keys
    iter_keys = sorted([i for i in dictionary.keys() if isinstance(i, int)])
    #If the list is empty, return the start value
    if not iter_keys:
        return start
    #Add an invalid value to the end of the list to make the loop exit before
    #raising StopIteration
    iter_keys.append(-1)
    #Create the iterator
    iter_keys = iter(iter_keys)
    #Start with the given number
    key = start
    #Add 1 to the key until it is not in the list
    while key == next(iter_keys): key += 1
    return key
