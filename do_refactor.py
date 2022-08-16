from helpers import elapsed_time, get_files, refactor


@elapsed_time
def main(debug=False):
    files, result_dir, total_count, workdir = get_files(debug)
    refactor(files, result_dir, total_count, workdir)


if __name__ == "__main__":
    main(debug=True)
