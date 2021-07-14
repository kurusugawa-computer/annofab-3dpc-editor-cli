from typing import Callable, List, Optional, TypeVar

import more_itertools

A = TypeVar("A")


class GenList:
    @staticmethod
    def gen_zoom_in(pred: Callable[[A], bool]) -> Callable[[List[A]], Optional[A]]:
        return lambda l: more_itertools.first_true(l, pred=pred)

    @staticmethod
    def gen_zoom_out(pred: Callable[[A], bool]) -> Callable[[List[A], Optional[A]], List[A]]:
        def zoom_out(a_list: List[A], a: Optional[A]) -> List[A]:
            index, _ = more_itertools.first_true(enumerate(a_list), pred=lambda ie: pred(ie[1]), default=(None, None))
            if index is None:
                if a is None:
                    pass
                else:
                    a_list.append(a)
            else:
                if a is None:
                    a_list.pop(index)
                else:
                    a_list[index] = a

            return a_list

        return zoom_out
