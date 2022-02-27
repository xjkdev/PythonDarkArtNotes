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
bool check_ndarray_dims(const py::array_t<float> &array, std::vector<int> expect_shape) {
  if(array.ndim() != expect_shape.size()) {
    return false;
  }
  for(size_t i=0;i<expect_shape.size();i++) {
    if(expect_shape[i] == -1) continue;
    else if(expect_shape[i] != array.shape(i)) return false;
  }
  return true;
}

/**
 * @brief check ndarray dtype.
 *  Format descriptors of integral are not same in 64bit system.
 *  Numpy and Pybind11 may use different descriptors for same type.
 *  Use this function to avoid problems.
 *
 * @tparam T expected dtype
 * @param info buffer info
 * @return true same dtype
 * @return false not same dtype
 */
template <class T>
inline bool check_dtype(const pybind11::buffer_info &info) {
  if ((info.format == "i" || info.format == "l" || info.format == "q") &&
      info.itemsize == sizeof(T) && std::is_signed<T>::value) {
    return true;
  } else if ((info.format == "I" || info.format == "L" || info.format == "Q") &&
             info.itemsize == sizeof(T) && std::is_unsigned<T>::value) {
    return true;
  } else if (info.format == pybind11::format_descriptor<T>::format()) {
    return true;
  } else {
    return false;
  }
}
