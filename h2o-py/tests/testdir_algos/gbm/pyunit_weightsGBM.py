import sys
sys.path.insert(1, "../../../")
import h2o
import random
import copy

def weights_check(ip,port):
    
    

    def check_same(data1, data2, min_rows_scale):
        gbm1_regression = h2o.gbm(x=data1[["displacement", "power", "weight", "acceleration", "year"]],
                                  y="economy",
                                  training_frame=data1,
                                  min_rows=5,
                                  ntrees=5,
                                  max_depth=5)
        gbm2_regression = h2o.gbm(x=data2[["displacement", "power", "weight", "acceleration", "year", "weights"]],
                                  y=data2["economy"],
                                  min_rows=5*min_rows_scale,
                                  weights_column=data2["weights"],
                                  ntrees=5,
                                  max_depth=5)
        gbm1_binomial = h2o.gbm(x=data1[["displacement", "power", "weight", "acceleration", "year"]],
                                y=data1["economy_20mpg"],
                                min_rows=5,
                                distribution="bernoulli",
                                ntrees=5,
                                max_depth=5)
        gbm2_binomial = h2o.gbm(x=data2[["displacement", "power", "weight", "acceleration", "year", "weights"]],
                                y=data2["economy_20mpg"],
                                weights_column="weights",
                                training_frame=data2,
                                min_rows=5*min_rows_scale,
                                distribution="bernoulli",
                                ntrees=5,
                                max_depth=5)
        gbm1_multinomial = h2o.gbm(x=data1[["displacement", "power", "weight", "acceleration", "year"]],
                                   y=data1["cylinders"],
                                   min_rows=5,
                                   distribution="multinomial",
                                   ntrees=5,
                                   max_depth=5)
        gbm2_multinomial = h2o.gbm(x=data2[["displacement", "power", "weight", "acceleration", "year", "weights"]],
                                   y=data2["cylinders"],
                                   weights_column="weights",
                                   training_frame=data2,
                                   min_rows=5*min_rows_scale,
                                   distribution="multinomial",
                                   ntrees=5,
                                   max_depth=5)

        reg1_mse = gbm1_regression.mse()
        reg2_mse = gbm2_regression.mse()
        bin1_auc = gbm1_binomial.auc()
        bin2_auc = gbm2_binomial.auc()
        mul1_mse = gbm1_multinomial.mse()
        mul2_mse = gbm2_multinomial.mse()

        print "MSE (regresson)   no weights vs. weights: {0}, {1}".format(reg1_mse, reg2_mse)
        print "AUC (binomial)    no weights vs. weights: {0}, {1}".format(bin1_auc, bin2_auc)
        print "MSE (multinomial) no weights vs. weights: {0}, {1}".format(mul1_mse, mul2_mse)

        assert abs(reg1_mse - reg2_mse) < 1e-6 * reg1_mse, "Expected mse's to be the same, but got {0}, and {1}".format(reg1_mse, reg2_mse)
        assert abs(bin1_auc - bin2_auc) < 1e-6 * bin1_auc, "Expected auc's to be the same, but got {0}, and {1}".format(bin1_auc, bin2_auc)
        assert abs(mul1_mse - mul1_mse) < 1e-6 * mul1_mse, "Expected auc's to be the same, but got {0}, and {1}".format(mul1_mse, mul2_mse)

    h2o_cars_data = h2o.import_file(h2o.locate("smalldata/junit/cars_20mpg.csv"))
    h2o_cars_data["economy_20mpg"] = h2o_cars_data["economy_20mpg"].asfactor()
    h2o_cars_data["cylinders"] = h2o_cars_data["cylinders"].asfactor()

    # uniform weights same as no weights
    random.seed(2222)
    weight = random.randint(1,10)
    uniform_weights = [[weight] for r in range(406)]
    h2o_uniform_weights = h2o.H2OFrame(python_obj=uniform_weights)
    h2o_uniform_weights.setNames(["weights"])
    h2o_data_uniform_weights = h2o_cars_data.cbind(h2o_uniform_weights)

    print "Checking that using uniform weights is equivalent to no weights:"
    print
    check_same(h2o_cars_data, h2o_data_uniform_weights, weight)

    # zero weights same as removed observations
    zero_weights = [[0] if random.randint(0,1) else [1] for r in range(406)]
    h2o_zero_weights = h2o.H2OFrame(python_obj=zero_weights)
    h2o_zero_weights.setNames(["weights"])
    h2o_data_zero_weights = h2o_cars_data.cbind(h2o_zero_weights)
    h2o_data_zeros_removed = h2o_cars_data[h2o_zero_weights["weights"] == 1]

    print "Checking that using some zero weights is equivalent to removing those observations:"
    print
    check_same(h2o_data_zeros_removed, h2o_data_zero_weights, 1)

    # doubled weights same as doubled observations
    doubled_weights = [[1] if random.randint(0,1) else [2] for r in range(406)]
    h2o_doubled_weights = h2o.H2OFrame(python_obj=doubled_weights)
    h2o_doubled_weights.setNames(["weights"])
    h2o_data_doubled_weights = h2o_cars_data.cbind(h2o_doubled_weights)

    doubled_data = h2o.as_list(h2o_cars_data, use_pandas=False)
    colnames = doubled_data.pop(0)
    for idx, w in enumerate(doubled_weights):
        if w[0] == 2: doubled_data.append(doubled_data[idx])
    h2o_data_doubled = h2o.H2OFrame(python_obj=doubled_data)
    h2o_data_doubled.setNames(colnames)

    h2o_data_doubled["economy_20mpg"] = h2o_data_doubled["economy_20mpg"].asfactor()
    h2o_data_doubled["cylinders"] = h2o_data_doubled["cylinders"].asfactor()
    h2o_data_doubled_weights["economy_20mpg"] = h2o_data_doubled_weights["economy_20mpg"].asfactor()
    h2o_data_doubled_weights["cylinders"] = h2o_data_doubled_weights["cylinders"].asfactor()

    print "Checking that doubling some weights is equivalent to doubling those observations:"
    print
    check_same(h2o_data_doubled, h2o_data_doubled_weights, 1)

    # TODO: random weights

    # TODO: all zero weights???

    # TODO: negative weights???

if __name__ == "__main__":
    h2o.run_test(sys.argv, weights_check)
