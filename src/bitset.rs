//! Fast 64-bit word-aligned bitset for sieve elimination.

#[derive(Clone, Debug)]
pub struct BitSet {
    words: Vec<u64>,
    size: usize,
}

impl BitSet {
    /// Creates a bitset of `size` bits, all initialized to `true` (unmarked/candidate).
    pub fn new_all_set(size: usize) -> Self {
        let num_words = (size + 63) / 64;
        let mut words = vec![!0u64; num_words];
        // Clear trailing unused bits in the last word
        let remainder = size % 64;
        if remainder != 0 && num_words > 0 {
            words[num_words - 1] = (1u64 << remainder) - 1;
        }
        Self { words, size }
    }

    /// Sets the bit at `index` to false (marking it composite / eliminated).
    #[inline(always)]
    pub fn clear(&mut self, index: usize) {
        if index < self.size {
            let word_idx = index >> 6;
            let bit_idx = index & 63;
            self.words[word_idx] &= !(1u64 << bit_idx);
        }
    }

    /// Checks if the bit at `index` is still set (surviving candidate).
    #[inline(always)]
    pub fn get(&self, index: usize) -> bool {
        if index < self.size {
            let word_idx = index >> 6;
            let bit_idx = index & 63;
            (self.words[word_idx] & (1u64 << bit_idx)) != 0
        } else {
            false
        }
    }

    /// Returns the total number of set bits (survivors).
    pub fn count_ones(&self) -> usize {
        self.words.iter().map(|w| w.count_ones() as usize).sum()
    }

    /// Returns the total capacity in bits.
    pub fn len(&self) -> usize {
        self.size
    }

    /// Iterates over all indices where the bit is set.
    pub fn iter_ones(&self) -> impl Iterator<Item = usize> + '_ {
        (0..self.size).filter(move |&i| self.get(i))
    }
}
