"""
©Rudina Subaih
Unify the raw trajectory file format to a unified format
"""
import argparse
import os

import numpy as np
import numpy.typing as npt
import pandas as pd
import sqlite3
import pedpy


def get_parser_args():
    """
    Required arguments from the user to input
    :return: parser of arguments
    """
    parser = argparse.ArgumentParser(description="transform the trajectories (x, y)")
    parser.add_argument(
        "-p",
        "--path",
        help="Enter the path to the directory containing the trajectory files"
    )
    parser.add_argument(
        "-n",
        "--fileName",
        help="Enter the names of the trajectory files",
        nargs="+"
    )
    parser.add_argument(
        "-deli",
        "--delimiter",
        help="Enter the delimiter of the trajectory file",
    )
    parser.add_argument(
        "-idIdx",
        "--idColIndex",
        type=int,
        help="Enter the id_col_index of the trajectory file",
    )
    parser.add_argument(
        "-frIdx",
        "--frColIndex",
        type=int,
        help="Enter the fr_col_index of the trajectory file",
    )
    parser.add_argument(
        "-xIdx",
        "--xColIndex",
        type=int,
        help="Enter the x_col_index of the trajectory file",
    )
    parser.add_argument(
        "-yIdx",
        "--yColIndex",
        default=None,
        type=int,
        help="Enter the y_col_index of the trajectory file",
    )
    parser.add_argument(
        "-zIdx",
        "--zColIndex",
        type=int,
        help="Enter the z_col_index of the trajectory file",
    )
    parser.add_argument(
        "-po",
        "--pathOutput",
        help="Enter the path to save the output"
    )
    return parser.parse_args()


def file_format(traj_data, id_col_index, fr_col_index, x_col_index,
                y_col_index, z_col_index):
    """
    make the format of the trajectory file
    #id  frame   x   y   z
    OR
    #id  time   x   y   z
    :param traj_data:
    :param id_col_index:
    :param fr_col_index:
    :param x_col_index:
    :param y_col_index:
    :param z_col_index:
    :return:
    """
    if id_col_index is None:
        raise ValueError('ERROR: you have to add pedestrian ID to the trajectory file.')

    if x_col_index is None:
        raise ValueError('ERROR: you have to add x-coordinate to the trajectory file.')

    if y_col_index is None:
        raise ValueError('ERROR: you have to add y-coordinate to the trajectory file.')

    # Specify the column indices by which you want to sort the rows
    column_indices = (id_col_index, x_col_index)

    # Get the indices that would sort the first column
    sorted_indices = np.lexsort((traj_data[:, column_indices[1]], traj_data[:, column_indices[0]]))

    # Sort the matrix based on the specified columns
    traj_data = traj_data[sorted_indices]

    if fr_col_index is None:
        # iterate over pedestrians and give them frame
        pedIDs = set(traj_data[:, id_col_index])
        frames = np.array([])
        for id in pedIDs:
            ped_data = traj_data[traj_data[:, id_col_index] == id]
            frames = np.append(frames, np.arange(ped_data.shape[0]))  # values from 0 to the length of ped. traj.
    else:
        frames = traj_data[:, fr_col_index]

    if z_col_index is None:
        z = np.zeros(traj_data.shape[0])  # values equal 0
    else:
        z = frames = traj_data[:, z_col_index]

    # Create a 2D NumPy matrix by stacking the 1D arrays vertically
    traj_data = np.column_stack((traj_data[:, id_col_index], frames, traj_data[:, x_col_index], traj_data[:, y_col_index], z))

    # sort based od id and fr because the previous data appears not aus_mix_sorted
    traj_data = traj_data[np.lexsort((traj_data[:, 1], traj_data[:, 0]))]

    return traj_data


def read_sqlite_file(traj_path, traj_file_name):
    """
    To read the trajectory data from .sqlite files
    :param traj_path: string. Path to the trajectory file
    :param traj_file_name: name of the file
    :return:
    """
    trajectory_file = "%s/%s" % (traj_path, traj_file_name)
    con = sqlite3.connect(trajectory_file)
    output_data = pd.read_sql_query(
        "select frame, id, pos_x as x, pos_y as y, ori_x as ox, ori_y as oy from trajectory_data",
        con,
    )
    # table in the SQLite database. The data is read into a Pandas DataFrame named data.
    return output_data


if __name__ == "__main__":
    arg = get_parser_args()
    path = arg.path
    files = arg.fileName
    path_output = arg.pathOutput
    delimiter = arg.delimiter
    id_col_index = arg.idColIndex
    fr_col_index = arg.frColIndex
    x_col_index = arg.xColIndex
    y_col_index = arg.yColIndex
    z_col_index = arg.zColIndex

    for file in files:
        print("Transforming: %s/%s" % (path, file))
        file_name = os.path.splitext(file)[0]
        file_type = os.path.splitext(file)[1]  # extension of the data file
        # format of the file
        if file_type == ".sqlite":
            data = read_sqlite_file(path, file)
            data = data.to_numpy()  # fr, pedID, x, y, ori_x, ori_y
        else:
            data = np.loadtxt("%s/%s" % (path, file), skiprows=1, delimiter=delimiter)

        data = file_format(data,
                           id_col_index,
                           fr_col_index,
                           x_col_index,
                           y_col_index,
                           z_col_index)

        header = "#id\tfr\tx\ty\tz"
        np.savetxt(
            "%s/%s_traj_file_format.txt" % (path_output, file_name),
            data,
            delimiter="\t",
            header=header,
            comments="",
            newline="\r\n",
            fmt="%d\t%d\t%.4f\t%.4f\t%.4f"
        )
