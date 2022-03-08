#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>

/**
 * @brief check ndarray dimensions
 *
 * @param array full array.
 * @param expect_shape expected shape, use -1 to address any size.
 * @return true ndarray matches expected shape.
 */
bool check_ndarray_dims(const py::array &array,
                        const std::vector<int> &expect_shape) {
  if (array.ndim() != expect_shape.size()) {
    return false;
  }
  for (size_t i = 0; i < expect_shape.size(); i++) {
    if (expect_shape[i] == -1)
      continue;
    else if (expect_shape[i] != array.shape(i))
      return false;
  }
  return true;
}

/**
 * @brief check ndarray dtype.
 *  Format descriptors of integral are not same in 64bit system.
 *  Numpy and Pybind11 may use different descriptors for same type,
 *  for example:
 *    64bit system, int64, numpy use l, pybind11 use q.
 *    32bit system, int64, numpy use q, pybind11 use q.
 *  Use this function to avoid problems.
 *
 * @tparam T expected dtype
 * @param info buffer info
 * @return true same dtype
 * @return false not same dtype
 */
template <class T, std::enable_if<std::is_arithmetic<T>::value, int>::type = 0>
inline bool check_dtype(const pybind11::buffer_info &info) {
  if (std::is_integral<T>::value && info.itemsize == sizeof(T)) {
    if (std::is_signed<T>::value &&
        (info.format == "i" || info.format == "l" || info.format == "q")) {
      return true;
    } else if (std::is_unsigned<T>::value &&
               (info.format == "I" || info.format == "L" ||
                info.format == "Q")) {
      return true;
    }
  }
  return info.format == pybind11::format_descriptor<T>::format();
}
