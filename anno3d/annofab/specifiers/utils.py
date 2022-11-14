from typing import Callable, List, Optional, TypeVar

import more_itertools

A = TypeVar("A")


class GenList:
    @staticmethod
    def gen_zoom_in(pred: Callable[[A], bool]) -> Callable[[List[A]], Optional[A]]:
        """Listの要素のうち最初に条件を満たす値を取得するzoom_inを生成する"""
        return lambda l: more_itertools.first_true(l, pred=pred)

    @staticmethod
    def gen_zoom_out(pred: Callable[[A], bool]) -> Callable[[List[A], Optional[A]], List[A]]:
        """Listの要素のうち最初に条件を満たす値を更新するzoom_outを生成する"""

        def zoom_out(a_list: List[A], a: Optional[A]) -> List[A]:
            """
            条件を最初に満たした要素を更新する。　条件を満たす要素がない場合、a_listの最後に値を追加する
            Args:
                a_list: 更新対象リスト
                a: 更新要素。 Noneの場合値を削除する。

            Returns:

            """
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
