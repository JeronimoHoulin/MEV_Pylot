// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

// Import necessary libraries and contracts
import "./IAggregationExecutor.sol";
import "./AggregationRouterV4.sol";

// Define the interface for the 1inch swap contract
interface IOneInchSwap {
    function swap(
        IAggregationExecutor caller,
        AggregationRouterV4.SwapDescription memory desc,
        bytes memory data
    ) external returns (uint256 returnAmount, uint256 gasLeft);
}

contract MyContract {
    // Address of the 1inch aggregator v5
    address private aggregatorV5 = 0x1111111254EEB25477B68fb85Ed929f73A960582;

    // Function to perform a swap using the 1inch aggregator
    function swap(
        IAggregationExecutor caller,
        AggregationRouterV4.SwapDescription memory desc,
        bytes memory data
    ) external returns (uint256 returnAmount, uint256 gasLeft) {
        // Call the swap function from the 1inch contract
        return IOneInchSwap(aggregatorV5).swap(caller, desc, data);
    }
}
