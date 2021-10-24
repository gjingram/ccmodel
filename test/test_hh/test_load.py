import orjson as json
import time


if __name__ == "__main__":
    tic = time.perf_counter()
    with open("parse_test-clang.json", "rb") as file_:
        data = json.loads(file_.read())
    toc = time.perf_counter()
    print(f"Load time: {toc - tic} [s]")

