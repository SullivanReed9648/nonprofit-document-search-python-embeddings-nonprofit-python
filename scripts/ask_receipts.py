from nonprofit_search.service import create_search


def main() -> None:
    search = create_search()
    search.build_index()
    result = search.search("What amount was on Maya Chen's donation receipt?", limit=1)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

