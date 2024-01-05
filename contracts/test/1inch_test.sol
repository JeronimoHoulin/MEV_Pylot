// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "../MiddlewareImplBase.sol";
import "../helpers/errors.sol";

/**
// @title One Inch Swap Implementation
// @notice Called by the registry before cross chain transfers if the user requests
// for a swap
// @dev Follows the interface of Swap Impl Base
// @author Movr Network
*/
contract OneInchSwapImpl is MiddlewareImplBase {
    using SafeERC20 for IERC20;

    event AmountRecieved(
        uint256 amount,
        address tokenAddress,
        address receiver
    );
    address private constant NATIVE_TOKEN_ADDRESS =
        address(0x0000000000000000000000000000000000001010);

    //address private constant INITIAL_OWNER =
    //    address(0x9E8680dbBcA1127add812abE209A10E621b385dF);

    //address private constant REGISTRY =
    //    address(0xc30141B657f4216252dc59Af2e7CdB9D8792e1B0);

    address private constant oneInchAggregator =
        payable(address(0x1111111254EEB25477B68fb85Ed929f73A960582)); //V5 !

    constructor(address initialOwner, address registry) MiddlewareImplBase(initialOwner, registry) {
    }

    /**
    // @notice Function responsible for swapping from one token to a different token
    // @dev This is called only when there is a request for a swap. 
    // @param from userAddress or sending address.
    // @param fromToken token to be swapped
    // @param amount amount to be swapped 
    // param to not required. This is there only to follow the MiddlewareImplBase
    // @param swapExtraData data required for the one inch aggregator to get the swap done
    */
    function oneInchSwapCall(
        address from,
        address fromToken,
        uint256 amount,
        address, // receiverAddress
        bytes memory swapExtraData
    ) external payable override onlyRegistry returns (uint256) {
        require(fromToken != address(0), MovrErrors.ADDRESS_0_PROVIDED);
        if (fromToken != NATIVE_TOKEN_ADDRESS) {
            IERC20(fromToken).safeTransferFrom(from, address(this), amount);
            IERC20(fromToken).safeIncreaseAllowance(oneInchAggregator, amount);
            {
                // solhint-disable-next-line
                (bool success, bytes memory result) = oneInchAggregator.call(
                    swapExtraData
                );
                IERC20(fromToken).approve(oneInchAggregator, 0);
                require(success, MovrErrors.MIDDLEWARE_ACTION_FAILED);
                (uint256 returnAmount, ) = abi.decode(
                    result,
                    (uint256, uint256)
                );
                return returnAmount;
            }
        } else {
            (bool success, bytes memory result) = oneInchAggregator.call{
                value: amount
            }(swapExtraData);
            require(success, MovrErrors.MIDDLEWARE_ACTION_FAILED);
            (uint256 returnAmount, ) = abi.decode(result, (uint256, uint256));
            return returnAmount;
        }
    }

    /**
    // @notice Function responsible for swapping from one token to a different token directly
    // @dev This is called only when there is a request for a swap. 
    // @param fromToken token to be swapped
    // @param amount amount to be swapped 
    // @param swapExtraData data required for the one inch aggregator to get the swap done
    */
    function oneInchSwap(
        address fromToken,
        address toToken,
        address receiver,
        uint256 amount,
        bytes memory swapExtraData
    ) external payable {
        if (fromToken != NATIVE_TOKEN_ADDRESS) {
            IERC20(fromToken).safeTransferFrom(
                msg.sender,
                address(this),
                amount
            );
            IERC20(fromToken).safeIncreaseAllowance(oneInchAggregator, amount);
            {
                // solhint-disable-next-line
                (bool success, bytes memory result) = oneInchAggregator.call(
                    swapExtraData
                );
                IERC20(fromToken).approve(oneInchAggregator, 0);
                require(success, MovrErrors.MIDDLEWARE_ACTION_FAILED);
                (uint256 returnAmount, ) = abi.decode(
                    result,
                    (uint256, uint256)
                );
                emit AmountRecieved(returnAmount, toToken, receiver);
            }
        } else {
            (bool success, bytes memory result) = oneInchAggregator.call{
                value: amount
            }(swapExtraData);
            require(success, MovrErrors.MIDDLEWARE_ACTION_FAILED);
            (uint256 returnAmount, ) = abi.decode(result, (uint256, uint256));
            emit AmountRecieved(returnAmount, toToken, receiver);
        }
    }
}