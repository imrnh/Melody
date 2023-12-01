import hashlib


class TextProcessor:
    def __init__(self) -> None:
        pass

    def substring_hashing(self, text):
        sha1 = hashlib.sha1()
        sha1.update(text.encode("utf-8"))
        return sha1.hexdigest()

    def filter_non_alpha_chars(self, text):
        result = ""
        for ch in text:
            if "a" <= ch <= "z" or "A" <= ch <= "Z" or ch == " ":
                result += ch
            else:
                result += ""
        return result

    def convert_to_integer(self, text):
        text_list = text.split(" ")
        text_sum = []
        for text in text_list:
            ch_sum = ""
            for idx, ch in enumerate(str(text)):
                ord_val = str(ord(ch) - 96)
                if len(ord_val) < 2:
                    ord_val = "0" + ord_val
                ch_sum += ord_val

            text_sum.append(ch_sum)

        return text_sum

    def shifting(self, windowed_text):
        res_text = ""
        for txt_intgr in windowed_text:
            res_text += txt_intgr
        return int(res_text)

    def line_transform(self, text):
        word_array = text.split(" ")
        window_size = 3 if len(word_array) >= 3 else len(word_array)
        unique_hashes_map = {}

        if window_size == 3:
            iteration_limit = len(word_array) - window_size + 1
        else:
            iteration_limit = 1

        for itr_idx in range(iteration_limit):
            internal_iteration_limit = len(word_array) - window_size + 1
            unique_hashes_map[window_size] = []  # initialize an empty list
            for iidx in range(internal_iteration_limit):
                sub_str_lst = word_array[iidx: iidx + window_size]
                sub_str = ' '.join(sub_str_lst)
                unq_hash = self.substring_hashing(sub_str)
                unique_hashes_map[window_size].append(unq_hash)
            window_size += 1  # after every iteration, increase window by 1

        return unique_hashes_map

    def transform(self, text):
        text = text.lower()
        text = self.filter_non_alpha_chars(text)
        hashes = self.line_transform(text)
        return hashes
